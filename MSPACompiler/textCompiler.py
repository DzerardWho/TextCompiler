from __future__ import annotations

from typing import Dict, List, Optional, Type, Union

from loguru import logger

from .parser import AST, caching_parser
from .parser import parse as input_str_to_ast
from .tags import BaseTag, Defines
from .tags.compiler import Compiler


class TextCompiler:
    '''This class is an entrypoint to the compiler'''

    def __init__(self, tag_definitions: str = ''):
        """Initialize compiler

        Parameters
        ----------
        tag_definitions : `str`, optional
            Initial language tags. They will be present in all text blocks
            created after loading then in, by default `''`
        """
        self.base_tag = BaseTag.new_instance(self)
        if tag_definitions:
            self.load_tags(tag_definitions)

    def load_tags(self, tag_definitions: Union[str, AST]):
        """Load new tag definitions.

        After loaded, they will be available in all newly created blocks.

        Parameters
        ----------
        tag_definitions : `Union[str, AST]`
            String containing tag definitions or already created AST.
        """
        ast = tag_definitions if not isinstance(tag_definitions, str) \
            else self.tags_to_ast(tag_definitions)
        self.__process_ast(ast, None)

    @staticmethod
    def tags_to_ast(tag_definitions: str) -> AST:
        """Generate AST of tag definitions.

        Parameters
        ----------
        tag_definitions : `str`
            String containing tag definitions.

        Returns
        -------
        `AST`
            Abstract syntax tree of tag definitions.
        """
        return [
            i
            for i in caching_parser(tag_definitions)
            if type(i) is dict and i['name'] == 'defines'
        ]

    def process_text(
            self,
            text: str,
            use_tmp_tags: Union[bool, Dict[str, Type[BaseTag]]] = True
    ) -> str:
        """Create abstract syntax tree from inputed text and pass it to futher
        compilation

        Parameters
        ----------
        text : `str`
            Input text

        use_tmp_tags : `bool`, optional
            If there are defined new tags in input text, make them available
            only while parsing this text, or save them permanently,
            by default `True`

        Returns
        -------
        `str`
            Compiled text
        """
        tmp_tags: Optional[Dict[str, Type[BaseTag]]] \
            = {} if use_tmp_tags else None
        ast: List = input_str_to_ast(text)
        result = self.__process_ast(ast, tmp_tags)
        if use_tmp_tags:
            self.base_tag.lua.reset_tmp_code(self.base_tag.lua_scope)
        return result

    def __process_ast(
            self,
            ast: List,
            tmp_tags: Dict[str, Type[BaseTag]] = None
    ) -> str:
        """Recursively process abstract syntax tree to build output text

        Parameters
        ----------
        ast : `List`
            Abstract syntax tree
        tmp_tags : `Dict[str, Type[BaseTag]]`, optional
            Dictionary for storing temporary tags created during processing of
            current input text

        Returns
        -------
        `str`
            Compiled text
        """
        out = []

        for i in ast:
            if type(i) is dict:
                name = i['name']
                lower_name = name.lower()
                if lower_name == 'defines':
                    Defines.parse(i, self.base_tag, tmp_tags)
                else:
                    if tmp_tags is not None and lower_name in tmp_tags:
                        tag = tmp_tags.get(lower_name)
                    else:
                        tag = self.base_tag.tags.get(lower_name)

                    if tag is None:
                        logger.info(f'Unknown tag: {name}')
                        continue

                    i['content'] = [
                        self.__process_ast(i['content'], tmp_tags)
                    ]

                    t = tag.compile(i)
                    if t:
                        out.extend(t)
            elif i:
                out.append(i)

        return ''.join(out)

    def compile(self, text: str) -> str:
        """Compile input text

        Parameters
        ----------
        text : `str`
            Text to be compiled

        Returns
        -------
        `str`
            Resulting text
        """
        text = self.process_text(text).strip()
        return Compiler.lt_gt_escaped_regex.sub(
            Compiler.replace_escaped_lt_gt,
            text
        )

    def compile_css(self) -> str:
        """Compile css pressent in loaded tags

        Returns
        -------
        `str`
            CSS text
        """
        out = []
        used = set()

        def compile(t: Dict[str, Type[BaseTag]]):
            for i in t.values():
                if i in used:
                    continue
                used.add(i)
                v = i.compile_css()
                if v:
                    out.append(v)

        compile(self.base_tag.tags)

        return '\n'.join(out)
