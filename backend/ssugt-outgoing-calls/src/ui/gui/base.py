class BaseGui:

    def run(self) -> None:
        raise NotImplementedError

    def _render(self) -> None:
        raise NotImplementedError
