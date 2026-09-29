"""The SRC folder that provides the GSEngine with its APIs"""

from . import (animation,
                assets,
                bullet,
                controls,
                entity,
                events,
                powerup,
                ui,
                update,
                starfield,
                stats,
                clock,
                states,
                decorators,
                initialize,
                logger)

try:
    from . import pack
except ImportError:
    pack = None

__all__ = [
    animation,
    assets,
    bullet,
    controls,
    entity,
    events,
    powerup,
    ui,
    update,
    starfield,
    stats,
    clock,
    states,
    decorators,
    initialize,
    logger,
]

if pack is not None:
    __all__.append(pack)