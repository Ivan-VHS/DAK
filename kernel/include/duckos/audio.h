#ifndef DUCKOS_AUDIO_H
#define DUCKOS_AUDIO_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define DUCKOS_AUDIO_MAX_DEVICES 8u
#define DUCKOS_AUDIO_MAX_CHANNELS 8u
#define DUCKOS_AUDIO_MAX_RATE 192000u
#define DUCKOS_AUDIO_MAX_BUFFER_BYTES 262144u

typedef enum {
    DUCKOS_AUDIO_U8 = 1,
    DUCKOS_AUDIO_S16_LE,
    DUCKOS_AUDIO_S24_LE,
    DUCKOS_AUDIO_S32_LE,
    DUCKOS_AUDIO_F32_LE
} DuckOsAudioSampleFormat;

typedef struct {
    uint32_t sample_rate;
    uint16_t channels;
    uint16_t format;
} DuckOsAudioFormat;

typedef struct {
    const void *samples;
    uint64_t frame_count;
    void *completion_context;
    void (*completion)(void *context, int32_t status);
} DuckOsAudioBuffer;

typedef struct {
    void *context;
    int32_t (*open)(void *context, const DuckOsAudioFormat *format);
    int32_t (*submit)(void *context, const DuckOsAudioBuffer *buffer);
    int32_t (*pause)(void *context, int paused);
    int32_t (*close)(void *context);
} DuckOsAudioDriverV1;

typedef struct {
    uint32_t id;
    char name[32];
    DuckOsAudioFormat format;
    uint8_t registered;
    uint8_t opened;
} DuckOsAudioDeviceInfo;

/* PCM device services are part of DuckOS only; drivers retain hardware access. */
int32_t duckos_audio_register(const char *name, const DuckOsAudioDriverV1 *driver,
                              uint32_t *device_id);
int32_t duckos_audio_open(uint32_t device_id, const DuckOsAudioFormat *format);
int32_t duckos_audio_submit(uint32_t device_id, const DuckOsAudioBuffer *buffer);
int32_t duckos_audio_pause(uint32_t device_id, int paused);
int32_t duckos_audio_close(uint32_t device_id);
int32_t duckos_audio_device_info(uint32_t device_id, DuckOsAudioDeviceInfo *info);

#ifdef __cplusplus
}
#endif

#endif
