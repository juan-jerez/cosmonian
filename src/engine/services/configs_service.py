import json


class ConfigsService:
    def __init__(self) -> None:
        self._configs: dict[str, dict] = {}

    def get(self, path: str) -> dict:
        if path not in self._configs:
            with open(path, encoding="utf-8") as config_file:
                self._configs[path] = json.load(config_file)
        return self._configs[path]

    def reload(self, path: str) -> dict:
        """Vuelve a leer el archivo y descarta los cambios hechos en memoria (editor)."""
        self._configs.pop(path, None)
        return self.get(path)

    def save(self, path: str):
        """Escribe en el archivo la configuración tal como está en memoria (editor)."""
        with open(path, "w", encoding="utf-8") as config_file:
            json.dump(self._configs[path], config_file, indent=4, ensure_ascii=False)
