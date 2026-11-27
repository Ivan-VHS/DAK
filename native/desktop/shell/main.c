#define _POSIX_C_SOURCE 200809L

#include <EGL/egl.h>
#include <GLES2/gl2.h>
#include <errno.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <wayland-client.h>
#include <wayland-egl.h>
#include "xdg-shell-client-protocol.h"

struct duckos_shell {
    struct wl_display *display;
    struct wl_registry *registry;
    struct wl_compositor *compositor;
    struct xdg_wm_base *wm_base;
    struct wl_surface *surface;
    struct xdg_surface *xdg_surface;
    struct xdg_toplevel *toplevel;
    struct wl_callback *frame_callback;

    struct wl_egl_window *egl_window;
    EGLDisplay egl_display;
    EGLConfig egl_config;
    EGLContext egl_context;
    EGLSurface egl_surface;

    int width;
    int height;
    bool configured;
    bool frame_ready;
    bool running;
};

static void registry_global(void *data, struct wl_registry *registry,
                            uint32_t name, const char *interface,
                            uint32_t version)
{
    struct duckos_shell *shell = data;

    if (strcmp(interface, wl_compositor_interface.name) == 0) {
        uint32_t bind_version = version < 4 ? version : 4;
        shell->compositor = wl_registry_bind(
            registry, name, &wl_compositor_interface, bind_version);
    } else if (strcmp(interface, xdg_wm_base_interface.name) == 0) {
        uint32_t bind_version = version < 1 ? version : 1;
        shell->wm_base = wl_registry_bind(
            registry, name, &xdg_wm_base_interface, bind_version);
    }
}

static void registry_global_remove(void *data, struct wl_registry *registry,
                                  uint32_t name)
{
    (void)data;
    (void)registry;
    (void)name;
}

static const struct wl_registry_listener registry_listener = {
    .global = registry_global,
    .global_remove = registry_global_remove
};

static void wm_base_ping(void *data, struct xdg_wm_base *wm_base,
                         uint32_t serial)
{
    (void)data;
    xdg_wm_base_pong(wm_base, serial);
}

static const struct xdg_wm_base_listener wm_base_listener = {
    .ping = wm_base_ping
};

static void xdg_surface_configure(void *data, struct xdg_surface *xdg_surface,
                                  uint32_t serial)
{
    struct duckos_shell *shell = data;
    xdg_surface_ack_configure(xdg_surface, serial);
    shell->configured = true;
}

static const struct xdg_surface_listener surface_listener = {
    .configure = xdg_surface_configure
};

static void toplevel_configure(void *data, struct xdg_toplevel *toplevel,
                               int32_t width, int32_t height,
                               struct wl_array *states)
{
    (void)toplevel;
    (void)states;
    struct duckos_shell *shell = data;

    if (width > 0) {
        shell->width = width;
    }
    if (height > 0) {
        shell->height = height;
    }

    if (shell->egl_window != NULL) {
        wl_egl_window_resize(shell->egl_window, shell->width, shell->height, 0, 0);
    }
}

static void toplevel_close(void *data, struct xdg_toplevel *toplevel)
{
    (void)toplevel;
    struct duckos_shell *shell = data;
    shell->running = false;
}

static const struct xdg_toplevel_listener toplevel_listener = {
    .configure = toplevel_configure,
    .close = toplevel_close
};

static void frame_done(void *data, struct wl_callback *callback, uint32_t time)
{
    (void)time;
    struct duckos_shell *shell = data;
    shell->frame_ready = true;
    shell->frame_callback = NULL;
    wl_callback_destroy(callback);
}

static const struct wl_callback_listener frame_listener = {
    .done = frame_done
};

static bool connect_wayland(struct duckos_shell *shell)
{
    shell->display = wl_display_connect(NULL);
    if (shell->display == NULL) {
        fprintf(stderr, "duckos-shell: cannot connect to Wayland display\n");
        return false;
    }

    shell->registry = wl_display_get_registry(shell->display);
    if (shell->registry == NULL ||
        wl_registry_add_listener(shell->registry, &registry_listener, shell) < 0 ||
        wl_display_roundtrip(shell->display) < 0) {
        fprintf(stderr, "duckos-shell: cannot read Wayland globals\n");
        return false;
    }

    if (shell->compositor == NULL || shell->wm_base == NULL) {
        fprintf(stderr, "duckos-shell: compositor or xdg-shell global is missing\n");
        return false;
    }

    if (xdg_wm_base_add_listener(shell->wm_base, &wm_base_listener, shell) < 0) {
        return false;
    }

    shell->surface = wl_compositor_create_surface(shell->compositor);
    if (shell->surface == NULL) {
        return false;
    }

    shell->xdg_surface = xdg_wm_base_get_xdg_surface(shell->wm_base, shell->surface);
    if (shell->xdg_surface == NULL ||
        xdg_surface_add_listener(shell->xdg_surface, &surface_listener, shell) < 0) {
        return false;
    }

    shell->toplevel = xdg_surface_get_toplevel(shell->xdg_surface);
    if (shell->toplevel == NULL ||
        xdg_toplevel_add_listener(shell->toplevel, &toplevel_listener, shell) < 0) {
        return false;
    }

    xdg_toplevel_set_title(shell->toplevel, "DuckOS");
    xdg_toplevel_set_app_id(shell->toplevel, "org.ivanvhs.duckos");
    xdg_toplevel_set_min_size(shell->toplevel, 800, 520);
    wl_surface_commit(shell->surface);

    while (!shell->configured && shell->running) {
        if (wl_display_dispatch(shell->display) < 0) {
            fprintf(stderr, "duckos-shell: connection closed before configure\n");
            return false;
        }
    }

    return shell->running;
}

static bool create_egl_context(struct duckos_shell *shell)
{
    shell->egl_display = eglGetDisplay((EGLNativeDisplayType)shell->display);
    if (shell->egl_display == EGL_NO_DISPLAY) {
        fprintf(stderr, "duckos-shell: eglGetDisplay failed (0x%x)\n", eglGetError());
        return false;
    }

    EGLint major = 0;
    EGLint minor = 0;
    if (!eglInitialize(shell->egl_display, &major, &minor)) {
        fprintf(stderr, "duckos-shell: eglInitialize failed (0x%x)\n", eglGetError());
        return false;
    }

    if (!eglBindAPI(EGL_OPENGL_ES_API)) {
        fprintf(stderr, "duckos-shell: eglBindAPI failed (0x%x)\n", eglGetError());
        return false;
    }

    const EGLint config_attributes[] = {
        EGL_SURFACE_TYPE, EGL_WINDOW_BIT,
        EGL_RENDERABLE_TYPE, EGL_OPENGL_ES2_BIT,
        EGL_RED_SIZE, 8,
        EGL_GREEN_SIZE, 8,
        EGL_BLUE_SIZE, 8,
        EGL_ALPHA_SIZE, 8,
        EGL_NONE
    };

    EGLint config_count = 0;
    if (!eglChooseConfig(shell->egl_display, config_attributes,
                         &shell->egl_config, 1, &config_count) ||
        config_count == 0) {
        fprintf(stderr, "duckos-shell: no suitable EGL config (0x%x)\n", eglGetError());
        return false;
    }

    const EGLint context_attributes[] = {
        EGL_CONTEXT_CLIENT_VERSION, 2,
        EGL_NONE
    };

    shell->egl_context = eglCreateContext(
        shell->egl_display, shell->egl_config, EGL_NO_CONTEXT, context_attributes);
    if (shell->egl_context == EGL_NO_CONTEXT) {
        fprintf(stderr, "duckos-shell: eglCreateContext failed (0x%x)\n", eglGetError());
        return false;
    }

    shell->egl_window = wl_egl_window_create(shell->surface, shell->width, shell->height);
    if (shell->egl_window == NULL) {
        fprintf(stderr, "duckos-shell: could not create Wayland EGL window\n");
        return false;
    }

    shell->egl_surface = eglCreateWindowSurface(
        shell->egl_display, shell->egl_config,
        (EGLNativeWindowType)shell->egl_window, NULL);
    if (shell->egl_surface == EGL_NO_SURFACE) {
        fprintf(stderr, "duckos-shell: eglCreateWindowSurface failed (0x%x)\n", eglGetError());
        return false;
    }

    if (!eglMakeCurrent(shell->egl_display, shell->egl_surface,
                        shell->egl_surface, shell->egl_context)) {
        fprintf(stderr, "duckos-shell: eglMakeCurrent failed (0x%x)\n", eglGetError());
        return false;
    }

    eglSwapInterval(shell->egl_display, 1);

    const char *vendor = (const char *)glGetString(GL_VENDOR);
    const char *renderer = (const char *)glGetString(GL_RENDERER);
    const char *version = (const char *)glGetString(GL_VERSION);

    printf("DuckOS GL vendor: %s\n", vendor != NULL ? vendor : "unknown");
    printf("DuckOS GL renderer: %s\n", renderer != NULL ? renderer : "unknown");
    printf("DuckOS GL version: %s\n", version != NULL ? version : "unknown");

    if (renderer != NULL &&
        (strstr(renderer, "llvmpipe") != NULL ||
         strstr(renderer, "softpipe") != NULL ||
         strstr(renderer, "swrast") != NULL ||
         strstr(renderer, "SwiftShader") != NULL ||
         strstr(renderer, "Software Rasterizer") != NULL)) {
        puts("DuckOS graphics mode: software renderer");
    } else {
        puts("DuckOS graphics mode: EGL/GLES renderer active; verify device driver for hardware status");
    }

    return true;
}

static void draw_rect(int x, int y, int width, int height,
                      float red, float green, float blue)
{
    if (width <= 0 || height <= 0) {
        return;
    }

    glScissor(x, y, width, height);
    glClearColor(red, green, blue, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT);
}

static void draw_shell(struct duckos_shell *shell)
{
    const int width = shell->width;
    const int height = shell->height;
    const int sidebar = width < 920 ? 176 : 208;
    const int left = sidebar + 30;
    const int right = width - 30;
    const int content_width = right - left;
    const int gap = 14;
    const int card_width = (content_width - gap * 3) / 4;
    const int header_height = 62;
    const int metrics_y = height - header_height - 190;
    const int card_height = 112;

    glViewport(0, 0, width, height);
    glEnable(GL_SCISSOR_TEST);

    draw_rect(0, 0, width, height, 0.025f, 0.055f, 0.095f);
    draw_rect(0, 0, sidebar, height, 0.035f, 0.075f, 0.125f);
    draw_rect(sidebar, height - header_height, width - sidebar,
              header_height, 0.045f, 0.085f, 0.135f);

    draw_rect(24, height - 42, 112, 4, 0.22f, 0.75f, 0.98f);
    draw_rect(24, height - 112, sidebar - 48, 34, 0.075f, 0.16f, 0.24f);
    draw_rect(24, height - 158, sidebar - 48, 26, 0.055f, 0.12f, 0.19f);
    draw_rect(24, height - 196, sidebar - 48, 26, 0.055f, 0.12f, 0.19f);
    draw_rect(24, height - 234, sidebar - 48, 26, 0.055f, 0.12f, 0.19f);
    draw_rect(24, height - 272, sidebar - 48, 26, 0.055f, 0.12f, 0.19f);

    const int hero_y = height - header_height - 158;
    draw_rect(left, hero_y, content_width, 116, 0.055f, 0.13f, 0.21f);
    draw_rect(left + 20, hero_y + 82, 170, 5, 0.26f, 0.78f, 0.98f);
    draw_rect(left + 20, hero_y + 58, content_width / 3, 4, 0.24f, 0.43f, 0.57f);
    draw_rect(left + 20, hero_y + 38, content_width / 4, 4, 0.16f, 0.30f, 0.42f);
    draw_rect(right - 98, hero_y + 24, 72, 72, 0.09f, 0.30f, 0.45f);

    const float colors[4][3] = {
        {0.10f, 0.31f, 0.47f},
        {0.22f, 0.20f, 0.43f},
        {0.10f, 0.35f, 0.31f},
        {0.42f, 0.28f, 0.14f}
    };

    for (int i = 0; i < 4; ++i) {
        const int x = left + i * (card_width + gap);
        draw_rect(x, metrics_y - card_height, card_width, card_height,
                  0.055f, 0.11f, 0.17f);
        draw_rect(x + 14, metrics_y - 28, 34, 4,
                  colors[i][0], colors[i][1], colors[i][2]);
        draw_rect(x + 14, metrics_y - 62, card_width / 2, 12,
                  0.56f, 0.76f, 0.87f);
        draw_rect(x + 14, metrics_y - 88, card_width - 28, 4,
                  0.12f, 0.23f, 0.32f);
    }

    const int panel_y = 32;
    const int panel_height = metrics_y - card_height - panel_y - 18;
    const int panel_gap = 16;
    const int panel_width = (content_width - panel_gap) / 2;

    if (panel_height > 52) {
        draw_rect(left, panel_y, panel_width, panel_height,
                  0.045f, 0.095f, 0.15f);
        draw_rect(left + panel_width + panel_gap, panel_y,
                  panel_width, panel_height, 0.045f, 0.095f, 0.15f);
        draw_rect(left + 16, panel_y + panel_height - 26,
                  panel_width / 3, 4, 0.17f, 0.53f, 0.72f);
        draw_rect(left + panel_width + panel_gap + 16,
                  panel_y + panel_height - 26,
                  panel_width / 3, 4, 0.17f, 0.53f, 0.72f);
    }

    draw_rect(width / 2 - 118, 12, 236, 8, 0.075f, 0.16f, 0.24f);
    glDisable(GL_SCISSOR_TEST);
}

static bool run_shell(struct duckos_shell *shell)
{
    while (shell->running) {
        shell->frame_ready = false;
        shell->frame_callback = wl_surface_frame(shell->surface);

        if (shell->frame_callback != NULL) {
            wl_callback_add_listener(shell->frame_callback, &frame_listener, shell);
        }

        draw_shell(shell);

        if (!eglSwapBuffers(shell->egl_display, shell->egl_surface)) {
            fprintf(stderr, "duckos-shell: eglSwapBuffers failed (0x%x)\n", eglGetError());
            return false;
        }

        if (wl_display_flush(shell->display) < 0 && errno != EAGAIN) {
            fprintf(stderr, "duckos-shell: Wayland flush failed\n");
            return false;
        }

        while (shell->running && !shell->frame_ready &&
               shell->frame_callback != NULL) {
            if (wl_display_dispatch(shell->display) < 0) {
                shell->running = false;
                break;
            }
        }
    }

    return true;
}

static void destroy_shell(struct duckos_shell *shell)
{
    if (shell->egl_display != EGL_NO_DISPLAY) {
        eglMakeCurrent(shell->egl_display, EGL_NO_SURFACE, EGL_NO_SURFACE,
                       EGL_NO_CONTEXT);
        if (shell->egl_surface != EGL_NO_SURFACE) {
            eglDestroySurface(shell->egl_display, shell->egl_surface);
        }
        if (shell->egl_context != EGL_NO_CONTEXT) {
            eglDestroyContext(shell->egl_display, shell->egl_context);
        }
        eglTerminate(shell->egl_display);
    }

    if (shell->egl_window != NULL) {
        wl_egl_window_destroy(shell->egl_window);
    }
    if (shell->toplevel != NULL) {
        xdg_toplevel_destroy(shell->toplevel);
    }
    if (shell->xdg_surface != NULL) {
        xdg_surface_destroy(shell->xdg_surface);
    }
    if (shell->surface != NULL) {
        wl_surface_destroy(shell->surface);
    }
    if (shell->wm_base != NULL) {
        xdg_wm_base_destroy(shell->wm_base);
    }
    if (shell->compositor != NULL) {
        wl_compositor_destroy(shell->compositor);
    }
    if (shell->registry != NULL) {
        wl_registry_destroy(shell->registry);
    }
    if (shell->display != NULL) {
        wl_display_disconnect(shell->display);
    }
}

int main(void)
{
    struct duckos_shell shell = {
        .width = 1280,
        .height = 800,
        .egl_display = EGL_NO_DISPLAY,
        .egl_context = EGL_NO_CONTEXT,
        .egl_surface = EGL_NO_SURFACE,
        .running = true
    };

    if (!connect_wayland(&shell)) {
        destroy_shell(&shell);
        return EXIT_FAILURE;
    }

    if (!create_egl_context(&shell)) {
        destroy_shell(&shell);
        return EXIT_FAILURE;
    }

    puts("DuckOS native shell is using a Wayland EGL/GLES surface.");
    const bool success = run_shell(&shell);
    destroy_shell(&shell);
    return success ? EXIT_SUCCESS : EXIT_FAILURE;
}
