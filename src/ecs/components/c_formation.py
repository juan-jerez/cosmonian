import pygame


class CFormation:
    def __init__(self, formation_info: dict, captain_entity: int, members: list[int]) -> None:
        # El grupo vuela como uno solo: persigue al jugador y cada miembro ocupa su hueco
        self.max_speed: float = 0
        self.max_force: float = formation_info["max_force"]
        self.captain_entity = captain_entity
        self.members = members
        self.total_members = len(members)
        # Miembros que destruyó el jugador: si son todos, gana el bono de formación completa
        self.killed_by_player = 0
        self.full_bonus: int = formation_info["full_bonus"]
        # Rumbo del grupo (la figura se gira para mirar hacia él)
        self.heading = pygame.Vector2(0, -1)


class CFormationMember:
    def __init__(self, formation_entity: int, offset: pygame.Vector2, kind: str) -> None:
        self.formation_entity = formation_entity
        # Hueco en la figura con el grupo mirando hacia arriba; se gira según su rumbo
        self.offset = offset
        # Tipo de enemigo (I, P o E): si la formación se disuelve, vuela como uno normal
        self.kind = kind
