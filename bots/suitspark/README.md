# Suitspark

Short Deck Omaha-specific range candidate. It samples legal five-card opponent
hands, weights them by the exact preflop equity table and whether the opponent
raised preflop, evaluates exactly two hole plus three board cards, and limits
the conditioned estimate to a 25% blend with random-hand equity. Unknown
opponent strategies can invalidate its preflop-action likelihood model.
