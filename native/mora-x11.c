/*
 * Mora native X11 compositor and window manager.
 *
 * The compositor uses the X Composite extension and XRender; the same event
 * loop handles top-level mapping, focus, basic decorations and title dragging.
 * This is an X11 backend, not a Wayland compositor or a kernel display driver.
 */
#define _POSIX_C_SOURCE 200809L
#include <X11/Xlib.h>
#include <X11/Xatom.h>
#include <X11/keysym.h>
#include <X11/Xutil.h>
#include <X11/extensions/Xcomposite.h>
#include <X11/extensions/Xdamage.h>
#include <X11/extensions/Xfixes.h>
#include <X11/extensions/Xrender.h>
#include <X11/extensions/shape.h>
#include <signal.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define TITLE_HEIGHT 30
#define BORDER_WIDTH 1
#define MAX_TITLE 512

typedef struct Client {
    Window window;
    Window frame;
    Damage damage;
    int x;
    int y;
    unsigned int width;
    unsigned int height;
    bool dragging;
    int drag_x;
    int drag_y;
    int frame_x;
    int frame_y;
    struct Client *next;
} Client;

static Display *display;
static int screen_number;
static Window root;
static Window overlay;
static Picture overlay_picture;
static Atom wm_delete;
static Atom wm_protocols;
static Atom wm_state;
static Atom wm_selection;
static Atom net_active_window;
static Atom net_client_list;
static Atom net_wm_name;
static Atom utf8_string;
static int damage_event;
static Client *clients;
static Client *focused;
static volatile sig_atomic_t running = 1;
static bool x11_bad_access = false;
static unsigned long decoration = 0x33261d;
static unsigned long decoration_edge = 0xd58b3d;
static unsigned long title_text = 0xfff3e2;

static void stop_running(int signal_number) {
    (void)signal_number;
    running = 0;
}

static int ignore_x_errors(Display *connection, XErrorEvent *event) {
    (void)connection;
    if (event->error_code == BadAccess) {
        x11_bad_access = true;
    }
    return 0;
}

static Client *find_client(Window window) {
    for (Client *client = clients; client; client = client->next) {
        if (client->window == window || client->frame == window) {
            return client;
        }
    }
    return NULL;
}

static void set_wm_state(Window window, long state) {
    long values[2] = {state, None};
    XChangeProperty(display, window, wm_state, wm_state, 32, PropModeReplace,
                    (unsigned char *)values, 2);
}

static void update_client_list(void) {
    size_t count = 0;
    for (Client *client = clients; client; client = client->next) {
        count++;
    }
    Window *windows = count ? calloc(count, sizeof(*windows)) : NULL;
    if (count && !windows) {
        return;
    }
    size_t index = 0;
    for (Client *client = clients; client; client = client->next) {
        windows[index++] = client->window;
    }
    XChangeProperty(display, root, net_client_list, XA_WINDOW, 32,
                    PropModeReplace, (unsigned char *)windows, (int)count);
    free(windows);
}

static void draw_frame(Client *client) {
    if (!client || !client->frame) {
        return;
    }
    XWindowAttributes attributes;
    if (!XGetWindowAttributes(display, client->frame, &attributes)) {
        return;
    }
    GC gc = XCreateGC(display, client->frame, 0, NULL);
    if (!gc) {
        return;
    }

    XSetForeground(display, gc, decoration);
    XFillRectangle(display, client->frame, gc, 0, 0,
                   attributes.width, TITLE_HEIGHT);
    XSetForeground(display, gc, decoration_edge);
    XFillRectangle(display, client->frame, gc, 0, TITLE_HEIGHT - 2,
                   attributes.width, 2);

    char *name = NULL;
    bool fallback_name = !XFetchName(display, client->window, &name) || !name;
    if (fallback_name) {
        name = strdup("Mora application");
    }
    if (name) {
        XSetForeground(display, gc, title_text);
        XDrawString(display, client->frame, gc, 12, 20, name,
                    (int)strnlen(name, MAX_TITLE));
        if (fallback_name) {
            free(name);
        } else {
            XFree(name);
        }
    }
    XSetForeground(display, gc, title_text);
    XDrawString(display, client->frame, gc,
                attributes.width > 24 ? (int)attributes.width - 22 : 2,
                20, "x", 1);
    XFreeGC(display, gc);
}

static void focus_client(Client *client) {
    if (!client) {
        return;
    }
    focused = client;
    XRaiseWindow(display, client->frame);
    XSetInputFocus(display, client->window, RevertToPointerRoot, CurrentTime);
    XChangeProperty(display, root, net_active_window, XA_WINDOW, 32,
                    PropModeReplace, (unsigned char *)&client->window, 1);
    draw_frame(client);
}

static void send_delete(Client *client) {
    if (!client) {
        return;
    }
    Atom *protocols = NULL;
    int count = 0;
    bool supports_delete = false;
    if (XGetWMProtocols(display, client->window, &protocols, &count)) {
        for (int index = 0; index < count; index++) {
            if (protocols[index] == wm_delete) {
                supports_delete = true;
                break;
            }
        }
    }
    if (protocols) {
        XFree(protocols);
    }

    if (supports_delete) {
        XEvent event;
        memset(&event, 0, sizeof(event));
        event.xclient.type = ClientMessage;
        event.xclient.window = client->window;
        event.xclient.message_type = wm_protocols;
        event.xclient.format = 32;
        event.xclient.data.l[0] = (long)wm_delete;
        event.xclient.data.l[1] = CurrentTime;
        XSendEvent(display, client->window, False, NoEventMask, &event);
    } else {
        XKillClient(display, client->window);
    }
}

static void unmanage(Window window, bool destroyed) {
    Client **cursor = &clients;
    while (*cursor) {
        Client *client = *cursor;
        if (client->window == window || client->frame == window) {
            *cursor = client->next;
            if (client->damage) {
                XDamageDestroy(display, client->damage);
            }
            if (!destroyed) {
                XRemoveFromSaveSet(display, client->window);
                XReparentWindow(display, client->window, root, client->x, client->y);
            }
            if (client->frame) {
                XDestroyWindow(display, client->frame);
            }
            if (focused == client) {
                focused = NULL;
                XDeleteProperty(display, root, net_active_window);
            }
            free(client);
            update_client_list();
            return;
        }
        cursor = &client->next;
    }
}

static void manage(Window window) {
    if (find_client(window)) {
        XMapWindow(display, window);
        return;
    }

    XWindowAttributes attributes;
    if (!XGetWindowAttributes(display, window, &attributes)) {
        return;
    }
    if (attributes.override_redirect || attributes.map_state == IsUnmapped) {
        if (attributes.override_redirect) {
            XMapWindow(display, window);
        }
        if (attributes.override_redirect) {
            return;
        }
    }

    Client *client = calloc(1, sizeof(*client));
    if (!client) {
        XMapWindow(display, window);
        return;
    }
    client->window = window;
    client->x = attributes.x;
    client->y = attributes.y;
    client->width = attributes.width > 0 ? (unsigned int)attributes.width : 640U;
    client->height = attributes.height > 0 ? (unsigned int)attributes.height : 480U;

    client->frame = XCreateSimpleWindow(
        display, root, client->x, client->y,
        client->width, client->height + TITLE_HEIGHT,
        BORDER_WIDTH, decoration_edge, decoration
    );
    if (!client->frame) {
        free(client);
        XMapWindow(display, window);
        return;
    }

    XSelectInput(display, client->frame,
                 ExposureMask | ButtonPressMask | ButtonReleaseMask |
                 PointerMotionMask | StructureNotifyMask);
    XSelectInput(display, window, StructureNotifyMask | PropertyChangeMask);
    XAddToSaveSet(display, window);
    XSetWindowBorderWidth(display, window, 0);
    XReparentWindow(display, window, client->frame, 0, TITLE_HEIGHT);

    client->damage = XDamageCreate(display, client->frame, XDamageReportNonEmpty);
    client->next = clients;
    clients = client;

    XMapWindow(display, window);
    XMapWindow(display, client->frame);
    set_wm_state(window, NormalState);
    draw_frame(client);
    focus_client(client);
    update_client_list();
}

static void configure_client(XConfigureRequestEvent *request) {
    Client *client = find_client(request->window);
    if (!client) {
        XWindowChanges changes = {
            .x = request->x, .y = request->y,
            .width = request->width, .height = request->height,
            .border_width = request->border_width,
            .sibling = request->above, .stack_mode = request->detail
        };
        XConfigureWindow(display, request->window, request->value_mask, &changes);
        return;
    }

    if (request->value_mask & CWWidth) {
        client->width = request->width > 0 ? (unsigned int)request->width : 1U;
    }
    if (request->value_mask & CWHeight) {
        client->height = request->height > 0 ? (unsigned int)request->height : 1U;
    }
    XWindowChanges changes = {
        .width = (int)client->width,
        .height = (int)client->height
    };
    XConfigureWindow(display, client->window, CWWidth | CWHeight, &changes);
    XMoveResizeWindow(display, client->frame, client->x, client->y,
                      client->width, client->height + TITLE_HEIGHT);
    draw_frame(client);
}

static void repaint(void) {
    if (!overlay_picture || !overlay) {
        return;
    }
    XWindowAttributes screen_attributes;
    if (!XGetWindowAttributes(display, root, &screen_attributes)) {
        return;
    }
    XRenderColor clear = {0, 0, 0, 0};
    XRenderFillRectangle(display, PictOpSrc, overlay_picture, &clear,
                         0, 0, (unsigned int)screen_attributes.width,
                         (unsigned int)screen_attributes.height);

    Window returned_root = None;
    Window parent = None;
    Window *children = NULL;
    unsigned int child_count = 0;
    if (!XQueryTree(display, root, &returned_root, &parent, &children, &child_count)) {
        XFlush(display);
        return;
    }

    for (unsigned int index = 0; index < child_count; index++) {
        Window child = children[index];
        if (child == overlay) {
            continue;
        }
        XWindowAttributes attributes;
        if (!XGetWindowAttributes(display, child, &attributes) ||
            attributes.map_state != IsViewable) {
            continue;
        }
        XRenderPictFormat *format = XRenderFindVisualFormat(display, attributes.visual);
        if (!format) {
            continue;
        }
        Pixmap pixmap = XCompositeNameWindowPixmap(display, child);
        if (!pixmap) {
            continue;
        }
        XRenderPictureAttributes picture_attributes;
        memset(&picture_attributes, 0, sizeof(picture_attributes));
        picture_attributes.subwindow_mode = IncludeInferiors;
        Picture source = XRenderCreatePicture(
            display, pixmap, format, CPSubwindowMode, &picture_attributes
        );
        if (source) {
            XRenderComposite(
                display, PictOpOver, source, None, overlay_picture,
                0, 0, 0, 0, attributes.x, attributes.y,
                (unsigned int)attributes.width, (unsigned int)attributes.height
            );
            XRenderFreePicture(display, source);
        }
        XFreePixmap(display, pixmap);
    }
    if (children) {
        XFree(children);
    }
    XFlush(display);
}

static void handle_button_press(XButtonEvent *event) {
    Client *client = find_client(event->window);
    if (!client) {
        return;
    }
    focus_client(client);
    if (event->button != Button1) {
        return;
    }
    if (event->y < TITLE_HEIGHT) {
        if (event->x >= (int)client->width - 28) {
            send_delete(client);
            return;
        }
        client->dragging = true;
        client->drag_x = event->x_root;
        client->drag_y = event->y_root;
        client->frame_x = client->x;
        client->frame_y = client->y;
        XGrabPointer(display, client->frame, False,
                     ButtonReleaseMask | PointerMotionMask,
                     GrabModeAsync, GrabModeAsync, None, None, CurrentTime);
    }
}

static void handle_motion(XMotionEvent *event) {
    Client *client = find_client(event->window);
    if (!client || !client->dragging) {
        return;
    }
    int next_x = client->frame_x + event->x_root - client->drag_x;
    int next_y = client->frame_y + event->y_root - client->drag_y;
    client->x = next_x;
    client->y = next_y;
    XMoveWindow(display, client->frame, next_x, next_y);
}

static void handle_key(XKeyEvent *event) {
    KeySym symbol = XLookupKeysym(event, 0);
    if (!(event->state & Mod1Mask)) {
        return;
    }
    if (!focused) {
        return;
    }
    if (symbol == XK_F4) {
        send_delete(focused);
    } else if (symbol == XK_F9) {
        XUnmapWindow(display, focused->frame);
        set_wm_state(focused->window, IconicState);
        if (focused->next) {
            focus_client(focused->next);
        } else {
            XSetInputFocus(display, root, RevertToPointerRoot, CurrentTime);
        }
    }
}

static void initialise_ewmh(void) {
    wm_delete = XInternAtom(display, "WM_DELETE_WINDOW", False);
    wm_protocols = XInternAtom(display, "WM_PROTOCOLS", False);
    wm_state = XInternAtom(display, "WM_STATE", False);
    net_active_window = XInternAtom(display, "_NET_ACTIVE_WINDOW", False);
    net_client_list = XInternAtom(display, "_NET_CLIENT_LIST", False);
    net_wm_name = XInternAtom(display, "_NET_WM_NAME", False);
    utf8_string = XInternAtom(display, "UTF8_STRING", False);
    Atom check = XInternAtom(display, "_NET_SUPPORTING_WM_CHECK", False);
    Window supporting = XCreateSimpleWindow(display, root, -1, -1, 1, 1, 0, 0, 0);
    XChangeProperty(display, root, check, XA_WINDOW, 32, PropModeReplace,
                    (unsigned char *)&supporting, 1);
    XChangeProperty(display, supporting, check, XA_WINDOW, 32, PropModeReplace,
                    (unsigned char *)&supporting, 1);
    const char name[] = "Mora DuckOS Native X11 Compositor";
    XChangeProperty(display, supporting, net_wm_name, utf8_string, 8,
                    PropModeReplace, (const unsigned char *)name, (int)strlen(name));
    XMapWindow(display, supporting);
}

static bool check_extensions(void) {
    int event_base = 0;
    int error_base = 0;
    if (!XCompositeQueryExtension(display, &event_base, &error_base)) {
        fprintf(stderr, "DuckOS: X Composite extension is unavailable.\n");
        return false;
    }
    if (!XDamageQueryExtension(display, &damage_event, &error_base)) {
        fprintf(stderr, "DuckOS: X Damage extension is unavailable.\n");
        return false;
    }
    if (!XRenderQueryExtension(display, &event_base, &error_base)) {
        fprintf(stderr, "DuckOS: XRender extension is unavailable.\n");
        return false;
    }
    if (!XFixesQueryExtension(display, &event_base, &error_base)) {
        fprintf(stderr, "DuckOS: XFixes extension is unavailable.\n");
        return false;
    }
    return true;
}

static bool start_compositor(void) {
    int selection_screen = screen_number;
    char selection_name[64];
    snprintf(selection_name, sizeof(selection_name), "_NET_WM_CM_S%d", selection_screen);
    wm_selection = XInternAtom(display, selection_name, False);
    if (XGetSelectionOwner(display, wm_selection) != None) {
        fprintf(stderr, "DuckOS: another X11 compositor already owns %s.\n", selection_name);
        return false;
    }
    XSetSelectionOwner(display, wm_selection, root, CurrentTime);
    XSync(display, False);
    if (XGetSelectionOwner(display, wm_selection) != root) {
        fprintf(stderr, "DuckOS: could not acquire the X11 compositor selection.\n");
        return false;
    }

    x11_bad_access = false;
    XSelectInput(display, root,
                 SubstructureRedirectMask | SubstructureNotifyMask |
                 StructureNotifyMask | PropertyChangeMask);
    XSync(display, False);
    if (x11_bad_access) {
        fprintf(stderr, "DuckOS: another window manager already controls this X11 screen.\\n");
        return false;
    }
    XCompositeRedirectSubwindows(display, root, CompositeRedirectManual);
    overlay = XCompositeGetOverlayWindow(display, root);
    if (!overlay) {
        fprintf(stderr, "DuckOS: X Composite overlay could not be created.\n");
        return false;
    }
    XserverRegion empty_region = XFixesCreateRegion(display, NULL, 0);
    XFixesSetWindowShapeRegion(display, overlay, ShapeInput, 0, 0, empty_region);
    XFixesDestroyRegion(display, empty_region);
    XMapWindow(display, overlay);

    XRenderPictFormat *format = XRenderFindVisualFormat(display, DefaultVisual(display, screen_number));
    if (!format) {
        fprintf(stderr, "DuckOS: the root visual has no XRender format.\n");
        return false;
    }
    XRenderPictureAttributes attributes;
    memset(&attributes, 0, sizeof(attributes));
    attributes.subwindow_mode = IncludeInferiors;
    overlay_picture = XRenderCreatePicture(
        display, overlay, format, CPSubwindowMode, &attributes
    );
    if (!overlay_picture) {
        fprintf(stderr, "DuckOS: could not create the compositor target picture.\n");
        return false;
    }
    KeyCode close_key = XKeysymToKeycode(display, XK_F4);
    KeyCode minimize_key = XKeysymToKeycode(display, XK_F9);
    XGrabKey(display, close_key, Mod1Mask, root, False, GrabModeAsync, GrabModeAsync);
    XGrabKey(display, minimize_key, Mod1Mask, root, False, GrabModeAsync, GrabModeAsync);
    initialise_ewmh();
    XSync(display, False);
    return true;
}

static void cleanup(void) {
    for (Client *client = clients; client; ) {
        Client *next = client->next;
        if (client->damage) {
            XDamageDestroy(display, client->damage);
        }
        if (client->frame) {
            XDestroyWindow(display, client->frame);
        }
        free(client);
        client = next;
    }
    clients = NULL;
    if (overlay_picture) {
        XRenderFreePicture(display, overlay_picture);
    }
    if (overlay) {
        XCompositeReleaseOverlayWindow(display, root);
    }
    if (wm_selection) {
        XSetSelectionOwner(display, wm_selection, None, CurrentTime);
    }
    XCompositeUnredirectSubwindows(display, root, CompositeRedirectManual);
    XSync(display, False);
}

int main(int argc, char **argv) {
    bool check_only = argc == 2 && strcmp(argv[1], "--check") == 0;
    bool show_version = argc == 2 && strcmp(argv[1], "--version") == 0;
    if (argc > 2 || (argc == 2 && !check_only && !show_version)) {
        fprintf(stderr, "Usage: %s [--check|--version]\n", argv[0]);
        return 2;
    }
    if (show_version) {
        puts("DuckOS Mora X11 compositor 0.1.0");
        return 0;
    }
    display = XOpenDisplay(NULL);
    if (!display) {
        fprintf(stderr, "DuckOS: cannot open the active X11 display (DISPLAY is unset or inaccessible).\n");
        return 1;
    }
    screen_number = DefaultScreen(display);
    root = RootWindow(display, screen_number);
    XSetErrorHandler(ignore_x_errors);
    if (!check_extensions()) {
        XCloseDisplay(display);
        return 1;
    }
    if (check_only) {
        puts("DuckOS X11 compositor: X Composite, XDamage, XRender and XFixes are available.");
        XCloseDisplay(display);
        return 0;
    }
    if (!start_compositor()) {
        cleanup();
        XCloseDisplay(display);
        return 1;
    }

    signal(SIGINT, stop_running);
    signal(SIGTERM, stop_running);
    repaint();

    while (running) {
        XEvent event;
        XNextEvent(display, &event);
        if (event.type == MapRequest) {
            manage(event.xmaprequest.window);
            repaint();
        } else if (event.type == ConfigureRequest) {
            configure_client(&event.xconfigurerequest);
            repaint();
        } else if (event.type == DestroyNotify) {
            unmanage(event.xdestroywindow.window, true);
            repaint();
        } else if (event.type == UnmapNotify) {
            Client *client = find_client(event.xunmap.window);
            if (client && event.xunmap.window == client->window &&
                event.xunmap.event == client->frame) {
                set_wm_state(client->window, IconicState);
            }
            repaint();
        } else if (event.type == Expose) {
            Client *client = find_client(event.xexpose.window);
            if (client && event.xexpose.count == 0) {
                draw_frame(client);
            }
        } else if (event.type == ButtonPress) {
            handle_button_press(&event.xbutton);
            repaint();
        } else if (event.type == ButtonRelease) {
            Client *client = find_client(event.xbutton.window);
            if (client) {
                client->dragging = false;
            }
            XUngrabPointer(display, CurrentTime);
            repaint();
        } else if (event.type == MotionNotify) {
            handle_motion(&event.xmotion);
            repaint();
        } else if (event.type == KeyPress) {
            handle_key(&event.xkey);
        } else if (event.type == PropertyNotify) {
            Client *client = find_client(event.xproperty.window);
            if (client && event.xproperty.atom == XA_WM_NAME) {
                draw_frame(client);
                repaint();
            }
        } else if (event.type == damage_event + XDamageNotify) {
            XDamageNotifyEvent *damage = (XDamageNotifyEvent *)&event;
            Client *client = find_client(damage->drawable);
            if (client && client->damage) {
                XDamageSubtract(display, client->damage, None, None);
            }
            repaint();
        } else if (event.type == MappingNotify) {
            XRefreshKeyboardMapping(&event.xmapping);
        }
    }

    cleanup();
    XCloseDisplay(display);
    return 0;
}
