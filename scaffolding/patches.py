import falcon


__all__ = ["Request"]


class Request(falcon.Request):
    @property
    def media(self):
        # XXX @numberoverzero
        # XXX remove when https://github.com/falconry/falcon/issues/1234 is released to pypi
        # XXX otherwise an empty body "{}" will raise on second access
        if self._media is not None:
            return self._media

        handler = self.options.media_handlers.find_by_media_type(
            self.content_type,
            self.options.default_media_type
        )

        # Consume the stream
        raw = self.bounded_stream.read()

        # Deserialize and Return
        self._media = handler.deserialize(raw)
        return self._media
