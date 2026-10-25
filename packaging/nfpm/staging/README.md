# Staging tree for nfpm contents

Placeholder layout for channel **(a)** native packages. CI / release jobs fill this
tree with the real embedded `cp314t` interpreter, vendored layer-1 wheels, and
connector wheels before `nfpm package`.

| Path | Meaning |
| ---- | ------- |
| `usr/lib/data-boar/` | Product prefix (CPython + site-packages + layer 1) |
| `usr/lib/data-boar/extras/<extra>/` | Connector subpackage wheels (PYTHONPATH, same idea as container `/extras`) |
| `usr/bin/data-boar` | Wrapper invoking embedded interpreter |
| `etc/data-boar/` | Example config (`config\|noreplace`) |

Do not commit real interpreter binaries here.
