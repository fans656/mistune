from typing import Optional
from .core import BlockState
from .block_parser import BlockParser
from .inline_parser import InlineParser


class Markdown:
    """Markdown instance to convert markdown text into HTML or other formats.
    Here is an example with the HTMLRenderer::

        from mistune import HTMLRenderer

        md = Markdown(renderer=HTMLRenderer(escape=False))
        md('hello **world**')

    :param renderer: a renderer to convert parsed tokens
    :param block: block level syntax parser
    :param inline: inline level syntax parser
    :param plugins: mistune plugins to use
    """
    def __init__(self, renderer=None, block=None, inline=None, plugins=None):
        if block is None:
            block = BlockParser()

        if inline is None:
            inline = InlineParser()

        self.renderer = renderer
        self.block = block
        self.inline = inline
        self.before_parse_hooks = []
        self.before_render_hooks = []
        self.after_render_hooks = []

        if plugins:
            for plugin in plugins:
                plugin(self)

    def use(self, plugin):
        plugin(self)

    def render_state(self, state: BlockState):
        data = self._iter_render(state.tokens, state)
        if self.renderer:
            return self.renderer(data, state)
        return list(data)

    def _iter_render(self, tokens, state):
        for tok in tokens:
            if 'children' in tok:
                children = self._iter_render(tok['children'], state)
                tok['children'] = list(children)
            elif 'text' in tok:
                text = tok.pop('text')
                # process inline text
                tok['children'] = self.inline(text.strip(), state.env)
            yield tok

    def parse(self, s: str, state: Optional[BlockState]=None):
        """Parse and convert the given markdown string. If renderer is None,
        the returned **result** will be parsed markdown tokens.

        :param s: markdown string
        :param state: instance of BlockState
        :returns: result, state
        """
        if state is None:
            state = self.block.state_cls()

        # normalize line separator
        s = s.replace('\r\n', '\n')
        s = s.replace('\r', '\n')
        if not s.endswith('\n'):
            s += '\n'

        state.process(s)

        for hook in self.before_parse_hooks:
            hook(self, state)

        self.block.parse(state)

        for hook in self.before_render_hooks:
            hook(self, state)

        result = self.render_state(state)

        for hook in self.after_render_hooks:
            result = hook(self, result, state)
        return result, state

    def read(self, filepath, encoding='utf-8', state=None):
        if state is None:
            state = self.block.state_cls()

        state.env['__file__'] = filepath
        with open(filepath, 'rb') as f:
            s = f.read()

        s = s.decode(encoding)
        return self.parse(s, state)

    def __call__(self, s: str):
        if s is None:
            s = '\n'
        return self.parse(s)[0]
