#define _POSIX_C_SOURCE 200809L

#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#include <wayland-server-core.h>
#include <wlr/backend.h>
#include <wlr/render/allocator.h>
#include <wlr/render/wlr_renderer.h>
#include <wlr/types/wlr_compositor.h>
#include <wlr/types/wlr_output.h>
#include <wlr/types/wlr_scene.h>
#include <wlr/types/wlr_xdg_shell.h>
#include <wlr/util/log.h>

struct duckos_server;

struct duckos_output {
    struct wlr_output *wlr_output;
    struct wlr_scene_output *scene_output;
    struct wl_listener frame;
    struct wl_listener destroy;
};

struct duckos_server {
    struct wl_display *display;
    struct wlr_backend *backend;
    struct wlr_renderer *renderer;
    struct wlr_allocator *allocator;
    struct wlr_scene *scene;
    struct wlr_xdg_shell *xdg_shell;
    struct wl_listener new_output;
    struct wl_listener new_xdg_surface;
};

static void output_frame(struct wl_listener *listener, void *data)
{
    (void)data;
    struct duckos_output *output = wl_container_of(listener, output, frame);

    if (!wlr_scene_output_commit(output->scene_output, NULL)) {
        wlr_log(WLR_ERROR, "failed to commit output frame");
        return;
    }

    struct timespec now;
    if (clock_gettime(CLOCK_MONOTONIC, &now) == 0) {
        wlr_scene_output_send_frame_done(output->scene_output, &now);
    }
}

static void output_destroy(struct wl_listener *listener, void *data)
{
    (void)data;
    struct duckos_output *output = wl_container_of(listener, output, destroy);

    wl_list_remove(&output->frame.link);
    wl_list_remove(&output->destroy.link);
    free(output);
}

static void new_output(struct wl_listener *listener, void *data)
{
    struct duckos_server *server = wl_container_of(listener, server, new_output);
    struct wlr_output *wlr_output = data;

    if (!wlr_output_init_render(wlr_output, server->allocator, server->renderer)) {
        wlr_log(WLR_ERROR, "could not initialize rendering for output");
        return;
    }

    struct wlr_output_mode *mode = wlr_output_preferred_mode(wlr_output);
    struct wlr_output_state state;
    wlr_output_state_init(&state);
    wlr_output_state_set_enabled(&state, true);

    if (mode != NULL) {
        wlr_output_state_set_mode(&state, mode);
    }

    const bool output_ready = wlr_output_commit_state(wlr_output, &state);
    wlr_output_state_finish(&state);

    if (!output_ready) {
        wlr_log(WLR_ERROR, "could not enable output %s", wlr_output->name);
        return;
    }

    wlr_output_create_global(wlr_output, server->display);

    struct duckos_output *output = calloc(1, sizeof(*output));
    if (output == NULL) {
        wlr_log(WLR_ERROR, "out of memory while adding output");
        return;
    }

    output->wlr_output = wlr_output;
    output->scene_output = wlr_scene_output_create(server->scene, wlr_output);
    if (output->scene_output == NULL) {
        free(output);
        wlr_log(WLR_ERROR, "could not create scene output");
        return;
    }

    output->frame.notify = output_frame;
    wl_signal_add(&wlr_output->events.frame, &output->frame);

    output->destroy.notify = output_destroy;
    wl_signal_add(&wlr_output->events.destroy, &output->destroy);

    wlr_log(WLR_INFO, "output ready: %s (%dx%d)",
            wlr_output->name, wlr_output->width, wlr_output->height);
}

static void new_xdg_surface(struct wl_listener *listener, void *data)
{
    struct duckos_server *server =
        wl_container_of(listener, server, new_xdg_surface);
    struct wlr_xdg_surface *surface = data;

    wlr_scene_xdg_surface_create(&server->scene->tree, surface);
    wlr_log(WLR_INFO, "xdg-shell surface created");
}

static bool initialize_server(struct duckos_server *server)
{
    struct wl_event_loop *loop = wl_display_get_event_loop(server->display);

    server->backend = wlr_backend_autocreate(loop, NULL);
    if (server->backend == NULL) {
        wlr_log(WLR_ERROR, "no usable backend found");
        return false;
    }

    server->renderer = wlr_renderer_autocreate(server->backend);
    if (server->renderer == NULL) {
        wlr_log(WLR_ERROR, "could not create renderer");
        return false;
    }

    if (!wlr_renderer_init_wl_display(server->renderer, server->display)) {
        wlr_log(WLR_ERROR, "could not initialize renderer globals");
        return false;
    }

    server->allocator = wlr_allocator_autocreate(server->backend, server->renderer);
    if (server->allocator == NULL) {
        wlr_log(WLR_ERROR, "could not create buffer allocator");
        return false;
    }

    server->scene = wlr_scene_create();
    if (server->scene == NULL) {
        wlr_log(WLR_ERROR, "could not create scene");
        return false;
    }

    if (wlr_compositor_create(server->display, 5, server->renderer) == NULL) {
        wlr_log(WLR_ERROR, "could not create compositor global");
        return false;
    }

    server->xdg_shell = wlr_xdg_shell_create(server->display, 1);
    if (server->xdg_shell == NULL) {
        wlr_log(WLR_ERROR, "could not create xdg-shell global");
        return false;
    }

    server->new_output.notify = new_output;
    wl_signal_add(&server->backend->events.new_output, &server->new_output);

    server->new_xdg_surface.notify = new_xdg_surface;
    wl_signal_add(&server->xdg_shell->events.new_surface, &server->new_xdg_surface);

    return true;
}

static void destroy_server(struct duckos_server *server)
{
    if (server->display != NULL) {
        wl_display_destroy_clients(server->display);
    }

    if (server->backend != NULL) {
        wlr_backend_destroy(server->backend);
    }

    if (server->scene != NULL) {
        wlr_scene_node_destroy(&server->scene->tree.node);
    }

    if (server->allocator != NULL) {
        wlr_allocator_destroy(server->allocator);
    }

    if (server->renderer != NULL) {
        wlr_renderer_destroy(server->renderer);
    }

    if (server->display != NULL) {
        wl_display_destroy(server->display);
    }
}

int main(void)
{
    struct duckos_server server = {0};

    wlr_log_init(WLR_INFO, NULL);
    server.display = wl_display_create();
    if (server.display == NULL) {
        fprintf(stderr, "duckos-compositor: could not create Wayland display\n");
        return EXIT_FAILURE;
    }

    if (!initialize_server(&server)) {
        destroy_server(&server);
        return EXIT_FAILURE;
    }

    const char *socket_name = wl_display_add_socket_auto(server.display);
    if (socket_name == NULL) {
        wlr_log(WLR_ERROR, "could not create Wayland socket");
        destroy_server(&server);
        return EXIT_FAILURE;
    }

    if (!wlr_backend_start(server.backend)) {
        wlr_log(WLR_ERROR, "could not start backend");
        destroy_server(&server);
        return EXIT_FAILURE;
    }

    setenv("WAYLAND_DISPLAY", socket_name, 1);
    wlr_log(WLR_INFO, "DuckOS compositor listening on %s", socket_name);
    wlr_log(WLR_INFO, "rendering is provided by the selected wlroots/Mesa renderer");

    wl_display_run(server.display);
    destroy_server(&server);
    return EXIT_SUCCESS;
}
