#include "serein/serein.hpp"

#include <algorithm>
#include <array>
#include <cerrno>
#include <charconv>
#include <cctype>
#include <cstdlib>
#include <fstream>
#include <limits>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string_view>
#include <system_error>
#include <variant>

#ifdef _WIN32
#define NOMINMAX
#include <Windows.h>
#include <ShlObj.h>
#else
#include <fcntl.h>
#include <signal.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#if defined(__APPLE__)
#include <libproc.h>
#endif
#endif

namespace serein {
namespace {

namespace fs = std::filesystem;

struct JsonValue {
    using Array = std::vector<JsonValue>;
    using Object = std::map<std::string, JsonValue>;
    std::variant<std::nullptr_t, bool, double, std::string, Array, Object> value;
};

class JsonParser {
public:
    explicit JsonParser(std::string_view input) : input_(input) {}

    bool parse(JsonValue& value, std::string& error) {
        skipWhitespace();
        if (!parseValue(value, 0, error)) return false;
        skipWhitespace();
        if (position_ != input_.size()) return fail(error, "Unexpected data after the JSON value");
        return true;
    }

private:
    std::string_view input_;
    std::size_t position_ = 0;

    bool fail(std::string& error, const std::string& message) const {
        error = message + " at byte " + std::to_string(position_);
        return false;
    }

    void skipWhitespace() {
        while (position_ < input_.size()) {
            const char c = input_[position_];
            if (c != ' ' && c != '\t' && c != '\r' && c != '\n') break;
            ++position_;
        }
    }

    bool consume(char expected) {
        if (position_ >= input_.size() || input_[position_] != expected) return false;
        ++position_;
        return true;
    }

    bool parseValue(JsonValue& value, unsigned depth, std::string& error) {
        if (depth > 32) return fail(error, "JSON nesting is too deep");
        skipWhitespace();
        if (position_ >= input_.size()) return fail(error, "Unexpected end of JSON");

        switch (input_[position_]) {
        case '{': return parseObject(value, depth + 1, error);
        case '[': return parseArray(value, depth + 1, error);
        case '"': {
            std::string text;
            if (!parseString(text, error)) return false;
            value.value = std::move(text);
            return true;
        }
        case 't': return parseLiteral("true", JsonValue{true}, value, error);
        case 'f': return parseLiteral("false", JsonValue{false}, value, error);
        case 'n': return parseLiteral("null", JsonValue{nullptr}, value, error);
        default:
            if (input_[position_] == '-' || (input_[position_] >= '0' && input_[position_] <= '9')) {
                return parseNumber(value, error);
            }
            return fail(error, "Invalid JSON value");
        }
    }

    bool parseLiteral(std::string_view literal, JsonValue parsed, JsonValue& value, std::string& error) {
        if (input_.substr(position_, literal.size()) != literal) return fail(error, "Invalid JSON literal");
        position_ += literal.size();
        value = std::move(parsed);
        return true;
    }

    bool parseObject(JsonValue& value, unsigned depth, std::string& error) {
        consume('{');
        JsonValue::Object object;
        skipWhitespace();
        if (consume('}')) {
            value.value = std::move(object);
            return true;
        }

        while (position_ < input_.size()) {
            skipWhitespace();
            if (position_ >= input_.size() || input_[position_] != '"') {
                return fail(error, "Expected an object key");
            }

            std::string key;
            if (!parseString(key, error)) return false;
            skipWhitespace();
            if (!consume(':')) return fail(error, "Expected ':' after object key");

            JsonValue member;
            if (!parseValue(member, depth, error)) return false;
            if (!object.emplace(std::move(key), std::move(member)).second) {
                return fail(error, "Duplicate JSON object key");
            }

            skipWhitespace();
            if (consume('}')) {
                value.value = std::move(object);
                return true;
            }
            if (!consume(',')) return fail(error, "Expected ',' or '}' in object");
        }
        return fail(error, "Unterminated JSON object");
    }

    bool parseArray(JsonValue& value, unsigned depth, std::string& error) {
        consume('[');
        JsonValue::Array array;
        skipWhitespace();
        if (consume(']')) {
            value.value = std::move(array);
            return true;
        }

        while (position_ < input_.size()) {
            if (array.size() >= 128) return fail(error, "JSON array is too large");
            JsonValue member;
            if (!parseValue(member, depth, error)) return false;
            array.push_back(std::move(member));

            skipWhitespace();
            if (consume(']')) {
                value.value = std::move(array);
                return true;
            }
            if (!consume(',')) return fail(error, "Expected ',' or ']' in array");
        }
        return fail(error, "Unterminated JSON array");
    }

    static void appendUtf8(std::string& output, std::uint32_t codepoint) {
        if (codepoint <= 0x7f) {
            output.push_back(static_cast<char>(codepoint));
        } else if (codepoint <= 0x7ff) {
            output.push_back(static_cast<char>(0xc0 | (codepoint >> 6)));
            output.push_back(static_cast<char>(0x80 | (codepoint & 0x3f)));
        } else if (codepoint <= 0xffff) {
            output.push_back(static_cast<char>(0xe0 | (codepoint >> 12)));
            output.push_back(static_cast<char>(0x80 | ((codepoint >> 6) & 0x3f)));
            output.push_back(static_cast<char>(0x80 | (codepoint & 0x3f)));
        } else {
            output.push_back(static_cast<char>(0xf0 | (codepoint >> 18)));
            output.push_back(static_cast<char>(0x80 | ((codepoint >> 12) & 0x3f)));
            output.push_back(static_cast<char>(0x80 | ((codepoint >> 6) & 0x3f)));
            output.push_back(static_cast<char>(0x80 | (codepoint & 0x3f)));
        }
    }

    bool readHex4(std::uint32_t& value, std::string& error) {
        if (position_ + 4 > input_.size()) return fail(error, "Incomplete Unicode escape");
        value = 0;
        for (int i = 0; i < 4; ++i) {
            const char c = input_[position_++];
            value <<= 4;
            if (c >= '0' && c <= '9') value |= static_cast<std::uint32_t>(c - '0');
            else if (c >= 'a' && c <= 'f') value |= static_cast<std::uint32_t>(c - 'a' + 10);
            else if (c >= 'A' && c <= 'F') value |= static_cast<std::uint32_t>(c - 'A' + 10);
            else return fail(error, "Invalid Unicode escape");
        }
        return true;
    }

    bool parseString(std::string& output, std::string& error) {
        if (!consume('"')) return fail(error, "Expected a string");
        output.clear();

        while (position_ < input_.size()) {
            const unsigned char c = static_cast<unsigned char>(input_[position_++]);
            if (c == '"') return true;
            if (c < 0x20) return fail(error, "Control character inside a string");
            if (c != '\\') {
                output.push_back(static_cast<char>(c));
                continue;
            }
            if (position_ >= input_.size()) return fail(error, "Incomplete string escape");

            const char escaped = input_[position_++];
            switch (escaped) {
            case '"': output.push_back('"'); break;
            case '\\': output.push_back('\\'); break;
            case '/': output.push_back('/'); break;
            case 'b': output.push_back('\b'); break;
            case 'f': output.push_back('\f'); break;
            case 'n': output.push_back('\n'); break;
            case 'r': output.push_back('\r'); break;
            case 't': output.push_back('\t'); break;
            case 'u': {
                std::uint32_t codepoint = 0;
                if (!readHex4(codepoint, error)) return false;
                if (codepoint >= 0xd800 && codepoint <= 0xdbff) {
                    if (position_ + 2 > input_.size() || input_[position_] != '\\' || input_[position_ + 1] != 'u') {
                        return fail(error, "Missing low surrogate");
                    }
                    position_ += 2;
                    std::uint32_t low = 0;
                    if (!readHex4(low, error)) return false;
                    if (low < 0xdc00 || low > 0xdfff) return fail(error, "Invalid low surrogate");
                    codepoint = 0x10000 + ((codepoint - 0xd800) << 10) + (low - 0xdc00);
                } else if (codepoint >= 0xdc00 && codepoint <= 0xdfff) {
                    return fail(error, "Unexpected low surrogate");
                }
                appendUtf8(output, codepoint);
                break;
            }
            default: return fail(error, "Invalid string escape");
            }
        }
        return fail(error, "Unterminated JSON string");
    }

    bool parseNumber(JsonValue& value, std::string& error) {
        const std::size_t start = position_;
        if (position_ < input_.size() && input_[position_] == '-') ++position_;
        if (position_ >= input_.size()) return fail(error, "Incomplete JSON number");

        if (input_[position_] == '0') {
            ++position_;
        } else {
            if (input_[position_] < '1' || input_[position_] > '9') return fail(error, "Invalid JSON number");
            while (position_ < input_.size() && input_[position_] >= '0' && input_[position_] <= '9') ++position_;
        }

        if (position_ < input_.size() && input_[position_] == '.') {
            ++position_;
            const std::size_t fractionStart = position_;
            while (position_ < input_.size() && input_[position_] >= '0' && input_[position_] <= '9') ++position_;
            if (fractionStart == position_) return fail(error, "Invalid number fraction");
        }

        if (position_ < input_.size() && (input_[position_] == 'e' || input_[position_] == 'E')) {
            ++position_;
            if (position_ < input_.size() && (input_[position_] == '+' || input_[position_] == '-')) ++position_;
            const std::size_t exponentStart = position_;
            while (position_ < input_.size() && input_[position_] >= '0' && input_[position_] <= '9') ++position_;
            if (exponentStart == position_) return fail(error, "Invalid number exponent");
        }

        double number = 0;
        const auto text = input_.substr(start, position_ - start);
        const auto parsed = std::from_chars(text.data(), text.data() + text.size(), number);
        if (parsed.ec != std::errc{} || !std::isfinite(number)) return fail(error, "JSON number is out of range");
        value.value = number;
        return true;
    }
};

const JsonValue::Object* asObject(const JsonValue& value) {
    return std::get_if<JsonValue::Object>(&value.value);
}

const JsonValue::Array* asArray(const JsonValue& value) {
    return std::get_if<JsonValue::Array>(&value.value);
}

const std::string* asString(const JsonValue& value) {
    return std::get_if<std::string>(&value.value);
}

const bool* asBool(const JsonValue& value) {
    return std::get_if<bool>(&value.value);
}

bool hasOnlyKeys(const JsonValue::Object& object,
                 const std::set<std::string>& allowed,
                 const std::string& context,
                 std::string& error) {
    for (const auto& [key, ignored] : object) {
        (void)ignored;
        if (!allowed.contains(key)) {
            error = "Unknown property '" + key + "' in " + context;
            return false;
        }
    }
    return true;
}

bool readRequiredString(const JsonValue::Object& object,
                        const std::string& key,
                        std::size_t maxLength,
                        std::string& target,
                        std::string& error) {
    const auto it = object.find(key);
    if (it == object.end()) {
        error = "Missing required property '" + key + "'";
        return false;
    }
    const auto* value = asString(it->second);
    if (!value || value->empty() || value->size() > maxLength) {
        error = "Property '" + key + "' must be a non-empty string no longer than " + std::to_string(maxLength) + " bytes";
        return false;
    }
    target = *value;
    return true;
}

bool readOptionalString(const JsonValue::Object& object,
                        const std::string& key,
                        std::size_t maxLength,
                        std::string& target,
                        std::string& error) {
    const auto it = object.find(key);
    if (it == object.end()) return true;
    const auto* value = asString(it->second);
    if (!value || value->size() > maxLength) {
        error = "Property '" + key + "' must be a string no longer than " + std::to_string(maxLength) + " bytes";
        return false;
    }
    target = *value;
    return true;
}

bool readRequiredBool(const JsonValue::Object& object,
                      const std::string& key,
                      bool& target,
                      std::string& error) {
    const auto it = object.find(key);
    if (it == object.end()) {
        error = "Missing required property '" + key + "'";
        return false;
    }
    const auto* value = asBool(it->second);
    if (!value) {
        error = "Property '" + key + "' must be a boolean";
        return false;
    }
    target = *value;
    return true;
}

bool readStringArray(const JsonValue::Object& object,
                     const std::string& key,
                     std::size_t maxItems,
                     std::size_t maxLength,
                     std::vector<std::string>& output,
                     std::string& error,
                     bool required) {
    const auto it = object.find(key);
    if (it == object.end()) {
        if (required) {
            error = "Missing required array '" + key + "'";
            return false;
        }
        return true;
    }

    const auto* array = asArray(it->second);
    if (!array || array->size() > maxItems) {
        error = "Property '" + key + "' must be an array with at most " + std::to_string(maxItems) + " entries";
        return false;
    }

    std::set<std::string> seen;
    for (const auto& item : *array) {
        const auto* text = asString(item);
        if (!text || text->empty() || text->size() > maxLength) {
            error = "Every entry in '" + key + "' must be a non-empty string no longer than " + std::to_string(maxLength) + " bytes";
            return false;
        }
        if (key == "platforms" && !seen.insert(*text).second) {
            error = "Property 'platforms' cannot contain duplicates";
            return false;
        }
        output.push_back(*text);
    }
    return true;
}

bool validApplicationId(const std::string& id) {
    if (id.size() < 3 || id.size() > 128 || id.front() == '.' || id.back() == '.') return false;
    bool previousSeparator = true;
    for (const unsigned char c : id) {
        const bool alphanumeric = (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9');
        const bool separator = c == '.' || c == '-';
        if (!alphanumeric && !separator) return false;
        if (separator && previousSeparator) return false;
        previousSeparator = separator;
    }
    return !previousSeparator;
}

bool validProjectName(const std::string& project) {
    const auto slash = project.find('/');
    if (slash == std::string::npos || slash == 0 || slash + 1 >= project.size() ||
        project.find('/', slash + 1) != std::string::npos) return false;
    const auto validPart = [](std::string_view part) {
        return std::all_of(part.begin(), part.end(), [](unsigned char c) {
            return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
                   (c >= '0' && c <= '9') || c == '_' || c == '-' || c == '.';
        });
    };
    return validPart(std::string_view(project).substr(0, slash)) &&
           validPart(std::string_view(project).substr(slash + 1));
}

bool isOneOf(const std::string& value, std::initializer_list<std::string_view> options) {
    return std::any_of(options.begin(), options.end(), [&value](std::string_view option) {
        return value == option;
    });
}

bool readTextFile(const fs::path& path, std::string& content, std::string& error, std::size_t limit = 1024 * 1024) {
    std::error_code ec;
    const auto size = fs::file_size(path, ec);
    if (ec || size > limit) {
        error = ec ? "Cannot read file size: " + path.string() : "File exceeds the 1 MiB size limit: " + path.string();
        return false;
    }
    std::ifstream input(path, std::ios::binary);
    if (!input) {
        error = "Cannot open file: " + path.string();
        return false;
    }
    content.assign(std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>());
    if (!input.eof() && input.fail()) {
        error = "Could not read file completely: " + path.string();
        return false;
    }
    return true;
}

bool ensureDirectory(const fs::path& path, std::string& error) {
    std::error_code ec;
    fs::create_directories(path, ec);
    if (ec) {
        error = "Cannot create directory '" + path.string() + "': " + ec.message();
        return false;
    }
#ifndef _WIN32
    fs::permissions(path, fs::perms::owner_all, fs::perm_options::replace, ec);
    if (ec) {
        error = "Cannot restrict registry directory permissions: " + ec.message();
        return false;
    }
#endif
    return true;
}

fs::path appsDirectory(const fs::path& registry) {
    return registry / "apps";
}

fs::path processLedgerPath(const fs::path& registry) {
    return registry / "processes.tsv";
}

class ProcessLock {
public:
    explicit ProcessLock(const fs::path& registry) {
#ifdef _WIN32
        const fs::path lockPath = registry / "processes.lock";
        handle_ = CreateFileW(lockPath.c_str(), GENERIC_READ | GENERIC_WRITE, 0, nullptr, OPEN_ALWAYS,
                              FILE_ATTRIBUTE_HIDDEN, nullptr);
        locked_ = handle_ != INVALID_HANDLE_VALUE;
#else
        const fs::path lockPath = registry / "processes.lock";
        descriptor_ = ::open(lockPath.c_str(), O_CREAT | O_RDWR, S_IRUSR | S_IWUSR);
        if (descriptor_ >= 0 && ::flock(descriptor_, LOCK_EX) == 0) locked_ = true;
        else if (descriptor_ >= 0) {
            ::close(descriptor_);
            descriptor_ = -1;
        }
#endif
    }

    ~ProcessLock() {
#ifdef _WIN32
        if (handle_ != INVALID_HANDLE_VALUE) CloseHandle(handle_);
#else
        if (descriptor_ >= 0) {
            if (locked_) ::flock(descriptor_, LOCK_UN);
            ::close(descriptor_);
        }
#endif
    }

    bool locked() const { return locked_; }

private:
    bool locked_ = false;
#ifdef _WIN32
    HANDLE handle_ = INVALID_HANDLE_VALUE;
#else
    int descriptor_ = -1;
#endif
};

bool readProcessLedger(const fs::path& registry, std::vector<ProcessRecord>& records, std::string& error) {
    const fs::path path = processLedgerPath(registry);
    std::error_code ec;
    if (!fs::exists(path, ec)) return true;

    std::ifstream input(path);
    if (!input) {
        error = "Cannot open Serein process ledger";
        return false;
    }

    std::string line;
    while (std::getline(input, line)) {
        if (line.empty()) continue;
        const auto first = line.find('\t');
        const auto second = first == std::string::npos ? first : line.find('\t', first + 1);
        if (first == std::string::npos || second == std::string::npos) continue;

        ProcessRecord record;
        const auto pidText = std::string_view(line).substr(0, first);
        const auto tokenText = std::string_view(line).substr(second + 1);
        const auto pidResult = std::from_chars(pidText.data(), pidText.data() + pidText.size(), record.processId);
        const auto tokenResult = std::from_chars(tokenText.data(), tokenText.data() + tokenText.size(), record.startToken);
        record.applicationId = line.substr(first + 1, second - first - 1);
        if (pidResult.ec != std::errc{} || pidResult.ptr != pidText.data() + pidText.size() ||
            tokenResult.ec != std::errc{} || tokenResult.ptr != tokenText.data() + tokenText.size() ||
            record.processId == 0 || !validApplicationId(record.applicationId)) continue;
        records.push_back(std::move(record));
    }
    return true;
}

bool writeProcessLedger(const fs::path& registry,
                        const std::vector<ProcessRecord>& records,
                        std::string& error) {
    const fs::path path = processLedgerPath(registry);
    const fs::path temporary = registry / "processes.tsv.tmp";
    {
        std::ofstream output(temporary, std::ios::binary | std::ios::trunc);
        if (!output) {
            error = "Cannot create Serein process ledger";
            return false;
        }
        for (const auto& record : records) {
            output << record.processId << '\t' << record.applicationId << '\t' << record.startToken << '\n';
        }
        output.flush();
        if (!output) {
            error = "Cannot write Serein process ledger";
            return false;
        }
    }
#ifndef _WIN32
    std::error_code permissionError;
    fs::permissions(temporary, fs::perms::owner_read | fs::perms::owner_write,
                    fs::perm_options::replace, permissionError);
#endif
    std::error_code ec;
#ifdef _WIN32
    fs::remove(path, ec);
    ec.clear();
#endif
    fs::rename(temporary, path, ec);
    if (ec) {
        error = "Cannot update Serein process ledger: " + ec.message();
        return false;
    }
    return true;
}

#ifndef _WIN32
std::uint64_t linuxProcessStartToken(std::uint64_t processId) {
#if defined(__linux__)
    std::ifstream input("/proc/" + std::to_string(processId) + "/stat");
    std::string content;
    if (!input || !std::getline(input, content)) return 0;
    const auto closeParen = content.rfind(')');
    if (closeParen == std::string::npos || closeParen + 2 >= content.size()) return 0;
    std::istringstream fields(content.substr(closeParen + 2));
    std::string field;
    for (int index = 0; index <= 19; ++index) {
        if (!(fields >> field)) return 0;
        if (index == 19) {
            std::uint64_t token = 0;
            const auto parsed = std::from_chars(field.data(), field.data() + field.size(), token);
            return parsed.ec == std::errc{} ? token : 0;
        }
    }
#elif defined(__APPLE__)
    struct proc_bsdinfo info {};
    const int result = proc_pidinfo(static_cast<int>(processId), PROC_PIDTBSDINFO, 0, &info, sizeof(info));
    if (result != sizeof(info)) return 0;
    return static_cast<std::uint64_t>(info.pbi_start_tvsec) * 1000000ULL +
           static_cast<std::uint64_t>(info.pbi_start_tvusec);
#endif
    return 0;
}
#endif

std::uint64_t processStartToken(std::uint64_t processId) {
#ifdef _WIN32
    HANDLE process = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, FALSE, static_cast<DWORD>(processId));
    if (!process) return 0;
    FILETIME creation{}, exit{}, kernel{}, user{};
    const BOOL ok = GetProcessTimes(process, &creation, &exit, &kernel, &user);
    CloseHandle(process);
    if (!ok) return 0;
    ULARGE_INTEGER token{};
    token.LowPart = creation.dwLowDateTime;
    token.HighPart = creation.dwHighDateTime;
    return token.QuadPart;
#else
    return linuxProcessStartToken(processId);
#endif
}

bool processIdentityMatches(const ProcessRecord& record) {
    if (record.startToken == 0) return false;
    return processStartToken(record.processId) == record.startToken;
}

std::string readRootFile(const fs::path& path) {
    std::ifstream input(path, std::ios::binary);
    std::string value;
    if (!input) return {};
    std::getline(input, value);
    return value;
}

std::string pathToUtf8(const fs::path& path) {
#if defined(_WIN32)
    const std::wstring wide = path.wstring();
    if (wide.empty()) return {};
    const int required = WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, wide.data(),
                                              static_cast<int>(wide.size()), nullptr, 0, nullptr, nullptr);
    if (required <= 0) return {};
    std::string output(static_cast<std::size_t>(required), '\0');
    if (WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, wide.data(), static_cast<int>(wide.size()),
                            output.data(), required, nullptr, nullptr) <= 0) return {};
    return output;
#else
    return path.string();
#endif
}

#ifdef _WIN32
std::wstring utf8ToWide(const std::string& value) {
    if (value.empty()) return {};
    const int size = MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, value.data(),
                                         static_cast<int>(value.size()), nullptr, 0);
    if (size <= 0) return {};
    std::wstring output(static_cast<std::size_t>(size), L'\0');
    if (MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, value.data(),
                            static_cast<int>(value.size()), output.data(), size) <= 0) return {};
    return output;
}

std::wstring quoteWindowsArgument(const std::wstring& argument) {
    if (!argument.empty() && argument.find_first_of(L" \t\n\v\"") == std::wstring::npos) return argument;
    std::wstring result = L"\"";
    std::size_t backslashes = 0;
    for (const wchar_t c : argument) {
        if (c == L'\\') {
            ++backslashes;
            continue;
        }
        if (c == L'"') {
            result.append(backslashes * 2 + 1, L'\\');
            result.push_back(L'"');
            backslashes = 0;
            continue;
        }
        result.append(backslashes, L'\\');
        backslashes = 0;
        result.push_back(c);
    }
    result.append(backslashes * 2, L'\\');
    result.push_back(L'"');
    return result;
}
#endif

bool hasExecutablePermission(const fs::path& path) {
#ifdef _WIN32
    (void)path;
    return true;
#else
    return ::access(path.c_str(), X_OK) == 0;
#endif
}

bool findOnPath(const std::vector<std::string>& names, fs::path& executable, std::string& error) {
    const char* pathValue = std::getenv("PATH");
    if (!pathValue) {
        error = "PATH is not set; cannot find the requested runtime";
        return false;
    }

#ifdef _WIN32
    constexpr char separator = ';';
#else
    constexpr char separator = ':';
#endif

    std::string paths(pathValue);
    std::size_t start = 0;
    while (start <= paths.size()) {
        const auto end = paths.find(separator, start);
        const std::string part = paths.substr(start, end == std::string::npos ? std::string::npos : end - start);
        if (!part.empty()) {
            const fs::path directory = fs::u8path(part);
            for (const auto& name : names) {
                fs::path candidate = directory / fs::u8path(name);
                std::error_code ec;
                if (fs::is_regular_file(candidate, ec) && !ec && hasExecutablePermission(candidate)) {
                    executable = fs::canonical(candidate, ec);
                    if (!ec) return true;
                }
#ifdef _WIN32
                if (candidate.extension().empty()) {
                    candidate += L".exe";
                    ec.clear();
                    if (fs::is_regular_file(candidate, ec) && !ec) {
                        executable = fs::canonical(candidate, ec);
                        if (!ec) return true;
                    }
                }
#endif
            }
        }
        if (end == std::string::npos) break;
        start = end + 1;
    }

    error = "Required runtime is not available on PATH";
    return false;
}

bool resolveRuntime(const std::string& runtime, fs::path& executable, std::string& error) {
    if (runtime == "python3") {
#ifdef _WIN32
        return findOnPath({"python3.exe", "python.exe"}, executable, error);
#else
        return findOnPath({"python3", "python"}, executable, error);
#endif
    }
    if (runtime == "python") {
#ifdef _WIN32
        return findOnPath({"python.exe", "python3.exe"}, executable, error);
#else
        return findOnPath({"python", "python3"}, executable, error);
#endif
    }
    if (runtime == "node") {
#ifdef _WIN32
        return findOnPath({"node.exe"}, executable, error);
#else
        return findOnPath({"node"}, executable, error);
#endif
    }
    error = "Runtime '" + runtime + "' is not on Serein's allowlist (python3, python, node)";
    return false;
}

bool currentPlatformIsAllowed(const Manifest& manifest, std::string& error) {
    const std::string current = platformName();
    if (std::find(manifest.platforms.begin(), manifest.platforms.end(), current) == manifest.platforms.end()) {
        error = "This application does not declare support for the current platform (" + current + ")";
        return false;
    }
    return true;
}

std::string selectedEntrypoint(const Manifest& manifest) {
    const auto found = std::find_if(manifest.platformEntrypoints.begin(), manifest.platformEntrypoints.end(),
                                    [](const auto& entry) { return entry.first == platformName(); });
    return found == manifest.platformEntrypoints.end() ? manifest.entrypoint : found->second;
}

bool validRelativePath(const fs::path& relative) {
    if (relative.empty() || relative.is_absolute() || relative.has_root_name() || relative.has_root_directory()) return false;
    for (const auto& component : relative) {
        if (component == "..") return false;
    }
    return true;
}

bool saveAppRecord(const Manifest& manifest,
                   const fs::path& root,
                   const std::string& manifestText,
                   const fs::path& registry,
                   std::string& error) {
    if (!ensureDirectory(registry, error) || !ensureDirectory(appsDirectory(registry), error)) return false;

    const fs::path destination = appsDirectory(registry) / fs::u8path(manifest.applicationId);
    std::error_code ec;
    if (!fs::create_directory(destination, ec)) {
        error = ec ? "Cannot create app registration: " + ec.message() : "Application is already registered";
        return false;
    }
#ifndef _WIN32
    fs::permissions(destination, fs::perms::owner_all, fs::perm_options::replace, ec);
#endif

    {
        std::ofstream output(destination / "manifest.json", std::ios::binary | std::ios::out);
        if (!output) {
            fs::remove(destination, ec);
            error = "Cannot save registered manifest";
            return false;
        }
        output.write(manifestText.data(), static_cast<std::streamsize>(manifestText.size()));
        output.flush();
        if (!output) {
            output.close();
            fs::remove(destination / "manifest.json", ec);
            fs::remove(destination, ec);
            error = "Cannot write registered manifest";
            return false;
        }
    }
#ifndef _WIN32
    fs::permissions(destination / "manifest.json", fs::perms::owner_read | fs::perms::owner_write,
                    fs::perm_options::replace, ec);
#endif
    {
        std::ofstream output(destination / "install-root.txt", std::ios::binary | std::ios::out);
        if (!output) {
            fs::remove(destination / "manifest.json", ec);
            fs::remove(destination, ec);
            error = "Cannot save application installation root";
            return false;
        }
        const std::string rootText = pathToUtf8(root);
        output.write(rootText.data(), static_cast<std::streamsize>(rootText.size()));
        output.put('\n');
        output.flush();
        if (!output) {
            output.close();
            fs::remove(destination / "manifest.json", ec);
            fs::remove(destination / "install-root.txt", ec);
            fs::remove(destination, ec);
            error = "Cannot write application installation root";
            return false;
        }
    }
#ifndef _WIN32
    fs::permissions(destination / "install-root.txt", fs::perms::owner_read | fs::perms::owner_write,
                    fs::perm_options::replace, ec);
#endif
    return true;
}

bool loadAppFromDirectory(const fs::path& directory,
                          const fs::path& registry,
                          RegisteredApp& app,
                          std::string& error) {
    std::error_code ec;
    if (fs::is_symlink(fs::symlink_status(directory, ec))) {
        error = "Symlinked app registry entries are not accepted";
        return false;
    }
    const fs::path base = fs::canonical(appsDirectory(registry), ec);
    if (ec) {
        error = "Application registry directory is unavailable";
        return false;
    }
    const fs::path canonicalDirectory = fs::canonical(directory, ec);
    if (ec || !pathIsWithin(base, canonicalDirectory)) {
        error = "Application registry entry is outside the registry";
        return false;
    }

    const fs::path manifestPath = directory / "manifest.json";
    const fs::path rootPath = directory / "install-root.txt";
    if (fs::is_symlink(fs::symlink_status(manifestPath, ec)) ||
        fs::is_symlink(fs::symlink_status(rootPath, ec))) {
        error = "Symlinked registration files are not accepted";
        return false;
    }

    std::string manifestText;
    if (!readTextFile(manifestPath, manifestText, error)) return false;
    if (!parseManifestText(manifestText, app.manifest, error)) return false;

    const std::string rootText = readRootFile(rootPath);
    if (rootText.empty()) {
        error = "Registered application has no installation root";
        return false;
    }
    app.installRoot = fs::canonical(fs::u8path(rootText), ec);
    if (ec || !fs::is_directory(app.installRoot, ec) || ec) {
        error = "Registered application installation root is unavailable";
        return false;
    }
    if (directory.filename().string() != app.manifest.applicationId) {
        error = "Registered application ID does not match its registry directory";
        return false;
    }
    app.manifestPath = manifestPath;
    return true;
}

std::vector<std::string> makeProcessArguments(const Manifest& manifest,
                                              const fs::path& executable,
                                              const fs::path& entrypoint,
                                              const std::vector<std::string>& extraArguments) {
    std::vector<std::string> arguments;
    arguments.reserve(1 + manifest.arguments.size() + extraArguments.size() + (manifest.runtime.empty() ? 0 : 1));
    arguments.push_back(pathToUtf8(executable));
    if (!manifest.runtime.empty()) arguments.push_back(pathToUtf8(entrypoint));
    arguments.insert(arguments.end(), manifest.arguments.begin(), manifest.arguments.end());
    arguments.insert(arguments.end(), extraArguments.begin(), extraArguments.end());
    return arguments;
}

#ifdef _WIN32
bool launchNativeProcess(const fs::path& executable,
                         const std::vector<std::string>& arguments,
                         const fs::path& workingDirectory,
                         bool foreground,
                         LaunchResult& result,
                         std::string& error) {
    std::wstring commandLine;
    for (std::size_t index = 0; index < arguments.size(); ++index) {
        if (index != 0) commandLine.push_back(L' ');
        const std::wstring wide = utf8ToWide(arguments[index]);
        if (wide.empty() && !arguments[index].empty()) {
            error = "An argument contains invalid UTF-8";
            return false;
        }
        commandLine += quoteWindowsArgument(wide);
    }
    if (commandLine.empty()) {
        error = "No executable was provided";
        return false;
    }

    STARTUPINFOW startup{};
    startup.cb = sizeof(startup);
    PROCESS_INFORMATION process{};
    const std::wstring executableWide = executable.wstring();
    const std::wstring workingWide = workingDirectory.wstring();
    DWORD flags = CREATE_NEW_PROCESS_GROUP;
    if (!foreground) flags |= DETACHED_PROCESS;

    const BOOL created = CreateProcessW(executableWide.c_str(), commandLine.data(), nullptr, nullptr,
                                        FALSE, flags, nullptr, workingWide.c_str(), &startup, &process);
    if (!created) {
        error = "CreateProcessW failed with Windows error " + std::to_string(GetLastError());
        return false;
    }

    result.processId = process.dwProcessId;
    FILETIME creation{}, exit{}, kernel{}, user{};
    if (GetProcessTimes(process.hProcess, &creation, &exit, &kernel, &user)) {
        ULARGE_INTEGER token{};
        token.LowPart = creation.dwLowDateTime;
        token.HighPart = creation.dwHighDateTime;
        result.startToken = token.QuadPart;
    }

    if (foreground) {
        WaitForSingleObject(process.hProcess, INFINITE);
    }
    CloseHandle(process.hThread);
    CloseHandle(process.hProcess);
    return true;
}
#else
bool launchNativeProcess(const fs::path& executable,
                         const std::vector<std::string>& arguments,
                         const fs::path& workingDirectory,
                         bool foreground,
                         LaunchResult& result,
                         std::string& error) {
    int errorPipe[2] = {-1, -1};
#if defined(__linux__) || defined(__APPLE__)
    if (::pipe(errorPipe) != 0) {
        error = "Cannot create process status pipe: " + std::string(std::strerror(errno));
        return false;
    }
    const int flags = ::fcntl(errorPipe[1], F_GETFD);
    if (flags < 0 || ::fcntl(errorPipe[1], F_SETFD, flags | FD_CLOEXEC) < 0) {
        error = "Cannot protect process status pipe";
        ::close(errorPipe[0]);
        ::close(errorPipe[1]);
        return false;
    }
#else
    error = "This platform does not yet have a Serein process backend";
    (void)executable;
    (void)arguments;
    (void)workingDirectory;
    (void)foreground;
    (void)result;
    return false;
#endif

    const pid_t pid = ::fork();
    if (pid < 0) {
        error = "fork failed: " + std::string(std::strerror(errno));
        ::close(errorPipe[0]);
        ::close(errorPipe[1]);
        return false;
    }

    if (pid == 0) {
        ::close(errorPipe[0]);
        auto childFailure = [&](int code) {
            (void)::write(errorPipe[1], &code, sizeof(code));
            ::_exit(127);
        };

        if (!foreground && ::setsid() < 0) childFailure(errno);
        if (::chdir(workingDirectory.c_str()) != 0) childFailure(errno);

        if (!foreground) {
            const int nullDescriptor = ::open("/dev/null", O_RDWR);
            if (nullDescriptor < 0) childFailure(errno);
            for (int target = STDIN_FILENO; target <= STDERR_FILENO; ++target) {
                if (::dup2(nullDescriptor, target) < 0) childFailure(errno);
            }
            if (nullDescriptor > STDERR_FILENO) ::close(nullDescriptor);
        }

        std::vector<char*> rawArguments;
        rawArguments.reserve(arguments.size() + 1);
        for (const auto& argument : arguments) rawArguments.push_back(const_cast<char*>(argument.c_str()));
        rawArguments.push_back(nullptr);
        ::execv(executable.c_str(), rawArguments.data());
        childFailure(errno);
    }

    ::close(errorPipe[1]);
    int childError = 0;
    ssize_t bytesRead = 0;
    do {
        bytesRead = ::read(errorPipe[0], &childError, sizeof(childError));
    } while (bytesRead < 0 && errno == EINTR);
    ::close(errorPipe[0]);

    if (bytesRead > 0) {
        int status = 0;
        (void)::waitpid(pid, &status, 0);
        error = "Could not start process: " + std::string(std::strerror(childError));
        return false;
    }
    if (bytesRead < 0) {
        error = "Could not confirm process start: " + std::string(std::strerror(errno));
        return false;
    }

    result.processId = static_cast<std::uint64_t>(pid);
    result.startToken = processStartToken(result.processId);

    if (foreground) {
        int status = 0;
        pid_t waited = -1;
        do {
            waited = ::waitpid(pid, &status, 0);
        } while (waited < 0 && errno == EINTR);
        if (waited < 0) {
            error = "waitpid failed: " + std::string(std::strerror(errno));
            return false;
        }
        if (WIFEXITED(status) && WEXITSTATUS(status) != 0) {
            error = "Application exited with status " + std::to_string(WEXITSTATUS(status));
            return false;
        }
        if (WIFSIGNALED(status)) {
            error = "Application was terminated by signal " + std::to_string(WTERMSIG(status));
            return false;
        }
    }
    return true;
}
#endif

bool terminateProcess(const ProcessRecord& record, std::string& error) {
    if (!processIdentityMatches(record)) {
        error = "The process is no longer running, or its PID has been reused";
        return false;
    }
#ifdef _WIN32
    HANDLE process = OpenProcess(PROCESS_TERMINATE | PROCESS_QUERY_LIMITED_INFORMATION, FALSE,
                                 static_cast<DWORD>(record.processId));
    if (!process) {
        error = "OpenProcess failed with Windows error " + std::to_string(GetLastError());
        return false;
    }
    FILETIME creation{}, exit{}, kernel{}, user{};
    ULARGE_INTEGER currentToken{};
    const BOOL gotTimes = GetProcessTimes(process, &creation, &exit, &kernel, &user);
    currentToken.LowPart = creation.dwLowDateTime;
    currentToken.HighPart = creation.dwHighDateTime;
    if (!gotTimes || currentToken.QuadPart != record.startToken) {
        CloseHandle(process);
        error = "Process identity changed before stop";
        return false;
    }
    const BOOL stopped = TerminateProcess(process, 1);
    const DWORD lastError = GetLastError();
    CloseHandle(process);
    if (!stopped) {
        error = "TerminateProcess failed with Windows error " + std::to_string(lastError);
        return false;
    }
#else
    if (::kill(static_cast<pid_t>(record.processId), SIGTERM) != 0) {
        error = "SIGTERM failed: " + std::string(std::strerror(errno));
        return false;
    }
#endif
    return true;
}

} // namespace

std::string platformName() {
#ifdef _WIN32
    return "windows";
#elif defined(__APPLE__)
    return "macos";
#elif defined(__linux__)
    return "linux";
#else
    return "unknown";
#endif
}

fs::path defaultRegistryPath() {
#ifdef _WIN32
    wchar_t* localAppData = nullptr;
    if (SUCCEEDED(SHGetKnownFolderPath(FOLDERID_LocalAppData, 0, nullptr, &localAppData)) && localAppData) {
        fs::path result(localAppData);
        CoTaskMemFree(localAppData);
        return result / "DuckOS" / "Mora" / "registry";
    }
    const char* profile = std::getenv("USERPROFILE");
    if (profile) return fs::u8path(profile) / "AppData" / "Local" / "DuckOS" / "Mora" / "registry";
#else
    const char* stateHome = std::getenv("XDG_DATA_HOME");
    if (stateHome && *stateHome) return fs::u8path(stateHome) / "duckos" / "mora" / "registry";
    const char* home = std::getenv("HOME");
    if (home && *home) return fs::u8path(home) / ".local" / "share" / "duckos" / "mora" / "registry";
#endif
    return fs::current_path() / ".duckos" / "mora" / "registry";
}

bool parseManifestText(const std::string& source, Manifest& manifest, std::string& error) {
    if (source.empty() || source.size() > 1024 * 1024) {
        error = "Manifest must be between 1 byte and 1 MiB";
        return false;
    }

    JsonValue root;
    JsonParser parser(source);
    if (!parser.parse(root, error)) return false;
    const auto* object = asObject(root);
    if (!object) {
        error = "Manifest root must be an object";
        return false;
    }
    if (!hasOnlyKeys(*object, {"$schema", "schema_version", "application_id", "project", "display_name",
                               "description", "launch", "policy", "maturity", "capabilities"},
                     "manifest", error)) return false;

    Manifest parsed;
    if (!readOptionalString(*object, "$schema", 240, parsed.schemaVersion, error)) return false;
    if (!readRequiredString(*object, "schema_version", 32, parsed.schemaVersion, error)) return false;
    if (parsed.schemaVersion != "1.0.0") {
        error = "Unsupported manifest schema version: " + parsed.schemaVersion;
        return false;
    }
    if (!readRequiredString(*object, "application_id", 128, parsed.applicationId, error) ||
        !validApplicationId(parsed.applicationId)) {
        if (error.empty()) error = "application_id has an invalid format";
        else error = "application_id has an invalid format";
        return false;
    }
    if (!readRequiredString(*object, "project", 160, parsed.project, error) ||
        !validProjectName(parsed.project)) {
        error = "project must use the owner/repository form";
        return false;
    }
    if (!readRequiredString(*object, "display_name", 80, parsed.displayName, error) ||
        !readRequiredString(*object, "description", 240, parsed.description, error)) return false;

    const auto launchIt = object->find("launch");
    if (launchIt == object->end() || !asObject(launchIt->second)) {
        error = "Manifest requires a launch object";
        return false;
    }
    const auto& launch = *asObject(launchIt->second);
    if (!hasOnlyKeys(launch, {"kind", "platforms", "entrypoint", "platform_entrypoints", "runtime", "arguments", "working_directory"},
                     "launch", error)) return false;
    if (!readRequiredString(launch, "kind", 32, parsed.launchKind, error) ||
        !isOneOf(parsed.launchKind, {"local_process", "static_entrypoint"})) {
        error = "launch.kind must be local_process or static_entrypoint";
        return false;
    }
    if (!readStringArray(launch, "platforms", 3, 16, parsed.platforms, error, true) ||
        !readRequiredString(launch, "entrypoint", 240, parsed.entrypoint, error) ||
        !readOptionalString(launch, "runtime", 80, parsed.runtime, error) ||
        !readOptionalString(launch, "working_directory", 240, parsed.workingDirectory, error) ||
        !readStringArray(launch, "arguments", 32, 240, parsed.arguments, error, false)) return false;

    const auto entrypointsIt = launch.find("platform_entrypoints");
    if (entrypointsIt != launch.end()) {
        const auto* entrypoints = asObject(entrypointsIt->second);
        if (!entrypoints) {
            error = "launch.platform_entrypoints must be an object";
            return false;
        }
        for (const auto& [platform, path] : *entrypoints) {
            const auto* value = asString(path);
            if (!isOneOf(platform, {"windows", "linux", "macos"}) || !value || value->empty() || value->size() > 240) {
                error = "Invalid platform-specific entry point";
                return false;
            }
            parsed.platformEntrypoints.emplace_back(platform, *value);
        }
    }
    for (const auto& platform : parsed.platforms) {
        if (!isOneOf(platform, {"windows", "linux", "macos"})) {
            error = "Unsupported platform name: " + platform;
            return false;
        }
    }
    for (const auto& [platform, path] : parsed.platformEntrypoints) {
        (void)path;
        if (std::find(parsed.platforms.begin(), parsed.platforms.end(), platform) == parsed.platforms.end()) {
            error = "A platform-specific entry point must also be listed in launch.platforms";
            return false;
        }
    }

    const auto policyIt = object->find("policy");
    if (policyIt == object->end() || !asObject(policyIt->second)) {
        error = "Manifest requires a policy object";
        return false;
    }
    const auto& policy = *asObject(policyIt->second);
    if (!hasOnlyKeys(policy, {"integration_policy", "confirmation_required", "shell_interpolation", "trust_source"},
                     "policy", error)) return false;
    if (!readRequiredString(policy, "integration_policy", 32, parsed.integrationPolicy, error) ||
        !isOneOf(parsed.integrationPolicy, {"required", "optional", "opt_in", "disabled", "not_applicable"})) {
        error = "policy.integration_policy has an unsupported value";
        return false;
    }
    if (!readRequiredBool(policy, "confirmation_required", parsed.confirmationRequired, error) ||
        !readRequiredBool(policy, "shell_interpolation", parsed.shellInterpolation, error)) return false;
    if (!parsed.confirmationRequired || parsed.shellInterpolation) {
        error = "Serein requires confirmation_required=true and shell_interpolation=false";
        return false;
    }
    if (!readOptionalString(policy, "trust_source", 64, parsed.trustSource, error)) return false;
    if (!parsed.trustSource.empty() &&
        !isOneOf(parsed.trustSource, {"operator_installed_project", "bundled_os_component"})) {
        error = "policy.trust_source has an unsupported value";
        return false;
    }

    const auto maturityIt = object->find("maturity");
    if (maturityIt == object->end() || !asObject(maturityIt->second)) {
        error = "Manifest requires a maturity object";
        return false;
    }
    const auto& maturity = *asObject(maturityIt->second);
    if (!hasOnlyKeys(maturity, {"maturity_status", "verification_status"}, "maturity", error)) return false;
    if (!readRequiredString(maturity, "maturity_status", 32, parsed.maturityStatus, error) ||
        !isOneOf(parsed.maturityStatus, {"specified", "planned", "partial", "implemented", "verified"}) ||
        !readRequiredString(maturity, "verification_status", 32, parsed.verificationStatus, error) ||
        !isOneOf(parsed.verificationStatus, {"not_run", "passed", "failed", "blocked", "skipped", "not_applicable"})) {
        error = "Manifest maturity or verification status has an unsupported value";
        return false;
    }
    if (!readStringArray(*object, "capabilities", 32, 80, parsed.capabilities, error, true)) return false;

    manifest = std::move(parsed);
    error.clear();
    return true;
}

bool parseManifestFile(const fs::path& path, Manifest& manifest, std::string& error) {
    std::string source;
    if (!readTextFile(path, source, error)) return false;
    return parseManifestText(source, manifest, error);
}

bool pathIsWithin(const fs::path& base, const fs::path& candidate) {
    const fs::path normalizedBase = base.lexically_normal();
    const fs::path normalizedCandidate = candidate.lexically_normal();
#ifdef _WIN32
    auto baseText = normalizedBase.wstring();
    auto candidateText = normalizedCandidate.wstring();
    std::transform(baseText.begin(), baseText.end(), baseText.begin(), towlower);
    std::transform(candidateText.begin(), candidateText.end(), candidateText.begin(), towlower);
    if (candidateText == baseText) return true;
    if (baseText.empty()) return false;
    if (baseText.back() != L'\\' && baseText.back() != L'/') baseText.push_back(L'\\');
    return candidateText.size() > baseText.size() && candidateText.compare(0, baseText.size(), baseText) == 0;
#else
    const fs::path relative = normalizedCandidate.lexically_relative(normalizedBase);
    if (relative.empty()) return normalizedCandidate == normalizedBase;
    const auto first = *relative.begin();
    return first != ".." && !relative.is_absolute();
#endif
}

bool resolveAppPath(const fs::path& installRoot,
                    const std::string& relativePath,
                    fs::path& resolved,
                    std::string& error) {
    const fs::path requested = fs::u8path(relativePath);
    if (!validRelativePath(requested)) {
        error = "Application paths must be relative and cannot contain '..'";
        return false;
    }

    std::error_code ec;
    const fs::path root = fs::canonical(installRoot, ec);
    if (ec || !fs::is_directory(root, ec) || ec) {
        error = "Application installation root is not an available directory";
        return false;
    }
    const fs::path candidate = fs::canonical(root / requested, ec);
    if (ec) {
        error = "Application path does not exist: " + relativePath;
        return false;
    }
    if (!pathIsWithin(root, candidate)) {
        error = "Application path resolves outside its registered installation root";
        return false;
    }
    resolved = candidate;
    error.clear();
    return true;
}

bool registerApplication(const fs::path& manifestPath,
                         const fs::path& installRoot,
                         const fs::path& registryPath,
                         std::string& error) {
    Manifest manifest;
    if (!parseManifestFile(manifestPath, manifest, error)) return false;
    if (manifest.launchKind != "local_process") {
        error = "Only local_process applications can be registered with Serein";
        return false;
    }
    if (manifest.integrationPolicy == "disabled" || manifest.integrationPolicy == "not_applicable") {
        error = "This manifest does not permit application registration";
        return false;
    }
    if (manifest.maturityStatus == "planned") {
        error = "A planned application cannot be registered";
        return false;
    }
    if (manifest.trustSource != "operator_installed_project") {
        error = "External registrations must declare operator_installed_project as their trust source";
        return false;
    }

    std::error_code ec;
    const fs::path root = fs::canonical(installRoot, ec);
    if (ec || !fs::is_directory(root, ec) || ec) {
        error = "The supplied installation root is not an existing directory";
        return false;
    }

    fs::path entrypoint;
    if (!resolveAppPath(root, selectedEntrypoint(manifest), entrypoint, error)) return false;
    if (!fs::is_regular_file(entrypoint, ec) || ec) {
        error = "The declared application entry point is not a regular file";
        return false;
    }

    std::string source;
    if (!readTextFile(manifestPath, source, error)) return false;
    if (!saveAppRecord(manifest, root, source, registryPath, error)) return false;
    error.clear();
    return true;
}

bool unregisterApplication(const std::string& applicationId,
                           const fs::path& registryPath,
                           std::string& error) {
    if (!validApplicationId(applicationId)) {
        error = "Invalid application ID";
        return false;
    }
    const fs::path directory = appsDirectory(registryPath) / fs::u8path(applicationId);
    std::error_code ec;
    if (fs::is_symlink(fs::symlink_status(directory, ec))) {
        error = "Refusing to remove a symlinked application registration";
        return false;
    }
    if (!fs::exists(directory, ec)) {
        error = "Application is not registered";
        return false;
    }
    const fs::path canonicalApps = fs::canonical(appsDirectory(registryPath), ec);
    const fs::path canonicalDirectory = fs::canonical(directory, ec);
    if (ec || !pathIsWithin(canonicalApps, canonicalDirectory)) {
        error = "Application registration path is outside the registry";
        return false;
    }

    fs::remove(directory / "manifest.json", ec);
    ec.clear();
    fs::remove(directory / "install-root.txt", ec);
    ec.clear();
    if (!fs::remove(directory, ec) || ec) {
        error = "Could not remove application registration: " + ec.message();
        return false;
    }
    return true;
}

std::vector<RegisteredApp> registeredApplications(const fs::path& registryPath,
                                                   std::vector<std::string>& warnings) {
    std::vector<RegisteredApp> applications;
    std::error_code ec;
    if (!fs::exists(appsDirectory(registryPath), ec)) return applications;
    if (ec) {
        warnings.push_back("Cannot inspect the application registry: " + ec.message());
        return applications;
    }

    for (const auto& entry : fs::directory_iterator(appsDirectory(registryPath), ec)) {
        if (ec) {
            warnings.push_back("Cannot read an application registry entry: " + ec.message());
            break;
        }
        if (!entry.is_directory(ec) || ec) continue;
        RegisteredApp app;
        std::string error;
        if (loadAppFromDirectory(entry.path(), registryPath, app, error)) {
            applications.push_back(std::move(app));
        } else {
            warnings.push_back(entry.path().filename().string() + ": " + error);
        }
    }
    std::sort(applications.begin(), applications.end(), [](const auto& left, const auto& right) {
        return left.manifest.applicationId < right.manifest.applicationId;
    });
    return applications;
}

bool findRegisteredApplication(const std::string& applicationId,
                               const fs::path& registryPath,
                               RegisteredApp& app,
                               std::string& error) {
    if (!validApplicationId(applicationId)) {
        error = "Invalid application ID";
        return false;
    }
    return loadAppFromDirectory(appsDirectory(registryPath) / fs::u8path(applicationId), registryPath, app, error);
}

bool launchApplication(const RegisteredApp& app,
                       const std::vector<std::string>& extraArguments,
                       bool foreground,
                       const fs::path& registryPath,
                       LaunchResult& result,
                       std::string& error) {
    const Manifest& manifest = app.manifest;
    if (manifest.launchKind != "local_process") {
        error = "This application is not a native process entry point";
        return false;
    }
    if (manifest.integrationPolicy == "disabled" || manifest.integrationPolicy == "not_applicable") {
        error = "The manifest's integration policy does not allow launching";
        return false;
    }
    if (manifest.maturityStatus == "planned") {
        error = "A planned application cannot be launched";
        return false;
    }
    if (!currentPlatformIsAllowed(manifest, error)) return false;
    if (extraArguments.size() > 32) {
        error = "At most 32 additional arguments are accepted";
        return false;
    }
    for (const auto& argument : extraArguments) {
        if (argument.size() > 4096 || argument.find('\0') != std::string::npos) {
            error = "An additional argument exceeds the 4096-byte limit or contains a NUL byte";
            return false;
        }
    }

    fs::path entrypoint;
    if (!resolveAppPath(app.installRoot, selectedEntrypoint(manifest), entrypoint, error)) return false;
    std::error_code ec;
    if (!fs::is_regular_file(entrypoint, ec) || ec) {
        error = "The registered entry point is not a regular file";
        return false;
    }

    fs::path workingDirectory = app.installRoot;
    if (!manifest.workingDirectory.empty()) {
        if (!resolveAppPath(app.installRoot, manifest.workingDirectory, workingDirectory, error)) return false;
        if (!fs::is_directory(workingDirectory, ec) || ec) {
            error = "The configured working directory is not a directory";
            return false;
        }
    }

    fs::path executable;
    if (manifest.runtime.empty()) {
        executable = entrypoint;
        if (!hasExecutablePermission(executable)) {
            error = "The application entry point does not have executable permission";
            return false;
        }
    } else if (!resolveRuntime(manifest.runtime, executable, error)) {
        return false;
    }

    const auto arguments = makeProcessArguments(manifest, executable, entrypoint, extraArguments);
    if (arguments.empty()) {
        error = "No process arguments were resolved";
        return false;
    }

    std::string lockError;
    if (!ensureDirectory(registryPath, lockError)) {
        error = lockError;
        return false;
    }
    ProcessLock lock(registryPath);
    if (!lock.locked()) {
        error = "Could not lock the Serein process ledger";
        return false;
    }

    if (!launchNativeProcess(executable, arguments, workingDirectory, foreground, result, error)) return false;
    if (foreground) return true;

    if (result.startToken == 0) {
        result.startToken = processStartToken(result.processId);
    }
    if (result.startToken == 0) {
        ProcessRecord untracked{result.processId, 0, manifest.applicationId};
        (void)terminateProcess(untracked, lockError);
        error = "The process started, but its identity could not be recorded safely; it was stopped";
        return false;
    }

    std::vector<ProcessRecord> records;
    if (!readProcessLedger(registryPath, records, error)) {
        ProcessRecord untracked{result.processId, result.startToken, manifest.applicationId};
        (void)terminateProcess(untracked, lockError);
        return false;
    }
    records.erase(std::remove_if(records.begin(), records.end(), [](const ProcessRecord& record) {
        return !processIdentityMatches(record);
    }), records.end());
    records.push_back({result.processId, result.startToken, manifest.applicationId});
    if (!writeProcessLedger(registryPath, records, error)) {
        ProcessRecord untracked{result.processId, result.startToken, manifest.applicationId};
        (void)terminateProcess(untracked, lockError);
        return false;
    }

    error.clear();
    return true;
}

std::vector<ProcessRecord> activeProcesses(const fs::path& registryPath,
                                           std::vector<std::string>& warnings) {
    std::vector<ProcessRecord> records;
    std::string error;
    if (!ensureDirectory(registryPath, error)) {
        warnings.push_back(error);
        return records;
    }
    ProcessLock lock(registryPath);
    if (!lock.locked()) {
        warnings.push_back("Could not lock the Serein process ledger");
        return records;
    }
    if (!readProcessLedger(registryPath, records, error)) {
        warnings.push_back(error);
        return {};
    }
    const auto oldSize = records.size();
    records.erase(std::remove_if(records.begin(), records.end(), [](const ProcessRecord& record) {
        return !processIdentityMatches(record);
    }), records.end());
    if (records.size() != oldSize) {
        if (!writeProcessLedger(registryPath, records, error)) warnings.push_back(error);
    }
    return records;
}

bool stopProcess(std::uint64_t processId,
                 const fs::path& registryPath,
                 std::string& error) {
    if (processId == 0 || processId > static_cast<std::uint64_t>(std::numeric_limits<std::uint32_t>::max())) {
        error = "Invalid process ID";
        return false;
    }
    ProcessLock lock(registryPath);
    if (!lock.locked()) {
        error = "Could not lock the Serein process ledger";
        return false;
    }

    std::vector<ProcessRecord> records;
    if (!readProcessLedger(registryPath, records, error)) return false;
    const auto found = std::find_if(records.begin(), records.end(), [processId](const ProcessRecord& record) {
        return record.processId == processId;
    });
    if (found == records.end()) {
        error = "PID is not tracked by Serein";
        return false;
    }
    if (!terminateProcess(*found, error)) return false;
    records.erase(found);
    return writeProcessLedger(registryPath, records, error);
}

std::string quoteForDisplay(const std::string& value) {
    std::string result = "\"";
    for (const char c : value) {
        if (c == '\\' || c == '"') result.push_back('\\');
        if (c == '\n') {
            result += "\\n";
        } else if (c == '\r') {
            result += "\\r";
        } else if (c == '\t') {
            result += "\\t";
        } else {
            result.push_back(c);
        }
    }
    result.push_back('"');
    return result;
}

} // namespace serein