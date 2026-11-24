package eventintel

import "encoding/json"

func RecordJSON(value Record) string {
	encoded, _ := json.Marshal(value)
	return string(encoded)
}
