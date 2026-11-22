project('duckos-compositor', 'c',
  version: '0.1.0',
  default_options: ['c_std=c11', 'warning_level=2'])

wayland_server = dependency('wayland-server')
wlroots = dependency('wlroots-0.18', version: '>=0.18.0')
threads = dependency('threads')

executable('duckos-compositor',
  'main.c',
  dependencies: [wayland_server, wlroots, threads],
  install: true,
  install_dir: get_option('bindir'))
