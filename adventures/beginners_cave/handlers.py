"""
Beginner's Cave — adventure-specific event handlers.
"""

from core.base_handlers import BaseAdventureHandlers

CYNTHIA_ID  = 3
CYNTHIA_REWARD = 50


class AdventureHandlers(BaseAdventureHandlers):

    def on_adventure_win(self) -> None:
        """Award Duke Luxom's reward if Cynthia was rescued and is with the party."""
        cynthia = next(
            (f for f in self.engine.player.followers if f.id == CYNTHIA_ID),
            None
        )
        if cynthia:
            self.engine.player.gold += CYNTHIA_REWARD
            print()
            print(self.engine.tc(
                f"Cynthia throws her arms around you. \"Father will be so relieved!\"",
                "desc"
            ))
            print(self.engine.tc(
                f"Upon your return, Duke Luxom presses {CYNTHIA_REWARD} gold coins "
                f"into your hand with tears in his eyes.",
                "desc"
            ))
            print(self.engine.tc(
                f"  +{CYNTHIA_REWARD} gold (Duke Luxom's reward)",
                "heal"
            ))
