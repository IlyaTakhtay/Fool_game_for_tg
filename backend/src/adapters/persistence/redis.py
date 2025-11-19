import msgspec
from backend.src.game.contracts.game_contract import PlayerAction
from backend.src.game.models.card import Card, Rank, Suit
from backend.src.game.models.game import FoolGame
from backend.src.game.models.player import Player, PlayerStatus


class RedisFoolGameAdapter:
    CARD_REGISTRY = [Card(r, s) for s in Suit for r in Rank]
    CARD_TO_ID = {card: idx for idx, card in enumerate(CARD_REGISTRY)}

    STATE_TO_ID = {
        "LobbyState": 0,
        "DealState": 1,
        "PlayRoundWithoutThrowState": 2,
        "GameOverState": 3,
    }
    ID_TO_STATE = {v: k for k, v in STATE_TO_ID.items()}

    encoder = msgspec.msgpack.Encoder()
    decoder = msgspec.msgpack.Decoder()

    @staticmethod
    def encode(game: FoolGame) -> bytes:
        data = {
            "g": game.game_id,
            "pl": game.players_limit,
            "p": [
                {
                    "i": p.id_,
                    "n": p.name,
                    "s": p.status.value,
                    "h": [RedisFoolGameAdapter._card_to_id(c) for c in p.get_cards()],
                }
                for p in game.players
            ],
            "d": [RedisFoolGameAdapter._card_to_id(c) for c in game.deck._cards],
            "tc": (
                RedisFoolGameAdapter._card_to_id(game.deck._trump_card)
                if game.deck._trump_card
                else None
            ),
            "ts": game.deck._trump_suit.value if game.deck._trump_suit else None,
            "t": [
                [
                    RedisFoolGameAdapter._card_to_id(pair["attack_card"]),
                    (
                        RedisFoolGameAdapter._card_to_id(pair["defend_card"])
                        if pair.get("defend_card")
                        else None
                    ),
                ]
                for pair in game.game_table.table_cards
            ],
            "a": game.current_attacker_idx,
            "df": game.current_defender_idx,
            "st": RedisFoolGameAdapter._state_to_id(game._current_state),
            "rd": (
                game.round_defender_status.value if game.round_defender_status else None
            ),
            "sh": game.state_history[:],
            "ls": game.loser_ids if game.loser_ids else None,
        }

        packed = RedisFoolGameAdapter.encoder.encode(data)
        return packed

    @staticmethod
    def decode(data: bytes) -> FoolGame:
        """Создаём объект FoolGame"""
        unpacked = RedisFoolGameAdapter.decoder.decode(data)

        game = FoolGame(game_id=unpacked["g"], players_limit=unpacked["pl"])

        for p_data in unpacked["p"]:
            player = Player(id_=p_data["i"], name=p_data["n"])
            player.status = PlayerStatus(p_data["s"])

            for card_id in p_data["h"]:
                player.add_card(RedisFoolGameAdapter._id_to_card(card_id))

            game.players.append(player)

        game.deck._trump_suit = (
            Suit(unpacked["ts"]) if unpacked["ts"] is not None else None
        )
        game.deck._trump_card = (
            RedisFoolGameAdapter._id_to_card(unpacked["tc"])
            if unpacked.get("tc") is not None
            else None
        )
        game.deck._cards = [
            RedisFoolGameAdapter._id_to_card(cid) for cid in unpacked["d"]
        ]

        game.game_table.table_cards = [
            {
                "attack_card": RedisFoolGameAdapter._id_to_card(pair[0]),
                "defend_card": (
                    RedisFoolGameAdapter._id_to_card(pair[1])
                    if pair[1] is not None
                    else None
                ),
            }
            for pair in unpacked["t"]
        ]

        game.current_attacker_id = (
            game.players[unpacked["a"]].id_ if unpacked["a"] is not None else None
        )
        game.current_defender_id = (
            game.players[unpacked["df"]].id_ if unpacked["df"] is not None else None
        )

        from backend.src.game.states.abc.states_abstractions import GameState
        from backend.src.game.states.lobby_state import LobbyState

        state_name = RedisFoolGameAdapter.ID_TO_STATE[unpacked["st"]]
        state_class = next(
            (s for s in GameState.__subclasses__() if s.__name__ == state_name),
            None,
        )
        if state_class:
            game._current_state = state_class(game)
        else:
            game._current_state = LobbyState(game)

        game.round_defender_status = (
            PlayerAction(unpacked["rd"]) if unpacked["rd"] else None
        )
        game.state_history = unpacked.get("sh", [])
        game.loser_ids = unpacked.get("ls")

        return game

    @staticmethod
    def _card_to_id(card: Card) -> int:
        return RedisFoolGameAdapter.CARD_TO_ID[card]

    @staticmethod
    def _id_to_card(card_id: int) -> Card:
        return RedisFoolGameAdapter.CARD_REGISTRY[card_id]

    @staticmethod
    def _state_to_id(state) -> int:
        return RedisFoolGameAdapter.STATE_TO_ID[state.__class__.__name__]
