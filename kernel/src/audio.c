#include "duckos/audio.h"
#include "duckos/arch_x86_64.h"

#include <stddef.h>
#include <string.h>

typedef struct {
    DuckOsAudioDeviceInfo info;
    DuckOsAudioDriverV1 driver;
} DuckOsAudioDevice;

static DuckOsAudioDevice devices[DUCKOS_AUDIO_MAX_DEVICES];

static int valid_format(const DuckOsAudioFormat *format) {
    if (format == NULL || format->sample_rate < 8000u ||
        format->sample_rate > DUCKOS_AUDIO_MAX_RATE ||
        format->channels == 0u || format->channels > DUCKOS_AUDIO_MAX_CHANNELS)
        return 0;
    return format->format >= DUCKOS_AUDIO_U8 &&
           format->format <= DUCKOS_AUDIO_F32_LE;
}

static uint32_t sample_size(uint16_t format) {
    switch (format) {
    case DUCKOS_AUDIO_U8: return 1u;
    case DUCKOS_AUDIO_S16_LE: return 2u;
    case DUCKOS_AUDIO_S24_LE: return 3u;
    case DUCKOS_AUDIO_S32_LE:
    case DUCKOS_AUDIO_F32_LE: return 4u;
    default: return 0u;
    }
}

int32_t duckos_audio_register(const char *name, const DuckOsAudioDriverV1 *driver,
                              uint32_t *device_id) {
    if (name == NULL || driver == NULL || device_id == NULL ||
        driver->open == NULL || driver->submit == NULL ||
        driver->pause == NULL || driver->close == NULL)
        return -1;
    size_t length = strlen(name);
    if (length == 0u || length >= sizeof devices[0].info.name) return -2;

    uint64_t flags = duckos_irq_save();
    for (uint32_t i = 0u; i < DUCKOS_AUDIO_MAX_DEVICES; ++i) {
        if (devices[i].info.registered) continue;
        memset(&devices[i], 0, sizeof devices[i]);
        memcpy(devices[i].info.name, name, length + 1u);
        devices[i].info.id = i;
        devices[i].info.registered = 1u;
        devices[i].driver = *driver;
        *device_id = i;
        duckos_irq_restore(flags);
        return 0;
    }
    duckos_irq_restore(flags);
    return -3;
}

int32_t duckos_audio_open(uint32_t device_id, const DuckOsAudioFormat *format) {
    if (device_id >= DUCKOS_AUDIO_MAX_DEVICES || !valid_format(format))
        return -1;
    uint64_t flags = duckos_irq_save();
    DuckOsAudioDevice *device = &devices[device_id];
    if (!device->info.registered || device->info.opened) {
        duckos_irq_restore(flags);
        return -2;
    }
    DuckOsAudioDriverV1 driver = device->driver;
    duckos_irq_restore(flags);
    if (driver.open(driver.context, format) != 0) return -3;
    flags = duckos_irq_save();
    device->info.format = *format;
    device->info.opened = 1u;
    duckos_irq_restore(flags);
    return 0;
}

int32_t duckos_audio_submit(uint32_t device_id, const DuckOsAudioBuffer *buffer) {
    if (device_id >= DUCKOS_AUDIO_MAX_DEVICES || buffer == NULL ||
        buffer->samples == NULL || buffer->frame_count == 0u)
        return -1;
    uint64_t flags = duckos_irq_save();
    DuckOsAudioDevice *device = &devices[device_id];
    if (!device->info.registered || !device->info.opened) {
        duckos_irq_restore(flags);
        return -2;
    }
    DuckOsAudioFormat format = device->info.format;
    DuckOsAudioDriverV1 driver = device->driver;
    duckos_irq_restore(flags);

    uint64_t bytes_per_frame = (uint64_t)format.channels * sample_size(format.format);
    if (bytes_per_frame == 0u ||
        buffer->frame_count > DUCKOS_AUDIO_MAX_BUFFER_BYTES / bytes_per_frame)
        return -3;
    return driver.submit(driver.context, buffer);
}

int32_t duckos_audio_pause(uint32_t device_id, int paused) {
    if (device_id >= DUCKOS_AUDIO_MAX_DEVICES) return -1;
    uint64_t flags = duckos_irq_save();
    DuckOsAudioDevice *device = &devices[device_id];
    if (!device->info.registered || !device->info.opened) {
        duckos_irq_restore(flags);
        return -2;
    }
    DuckOsAudioDriverV1 driver = device->driver;
    duckos_irq_restore(flags);
    return driver.pause(driver.context, paused != 0);
}

int32_t duckos_audio_close(uint32_t device_id) {
    if (device_id >= DUCKOS_AUDIO_MAX_DEVICES) return -1;
    uint64_t flags = duckos_irq_save();
    DuckOsAudioDevice *device = &devices[device_id];
    if (!device->info.registered || !device->info.opened) {
        duckos_irq_restore(flags);
        return -2;
    }
    DuckOsAudioDriverV1 driver = device->driver;
    duckos_irq_restore(flags);
    if (driver.close(driver.context) != 0) return -3;
    flags = duckos_irq_save();
    device->info.opened = 0u;
    memset(&device->info.format, 0, sizeof device->info.format);
    duckos_irq_restore(flags);
    return 0;
}

int32_t duckos_audio_device_info(uint32_t device_id, DuckOsAudioDeviceInfo *info) {
    if (device_id >= DUCKOS_AUDIO_MAX_DEVICES || info == NULL) return -1;
    uint64_t flags = duckos_irq_save();
    if (!devices[device_id].info.registered) {
        duckos_irq_restore(flags);
        return -2;
    }
    *info = devices[device_id].info;
    duckos_irq_restore(flags);
    return 0;
}
