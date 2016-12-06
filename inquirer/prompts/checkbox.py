# -*- coding: utf-8 -*-
"""
`checkbox` type question
"""
from __future__ import print_function, unicode_literals
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding.manager import KeyBindingManager
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.filters import IsDone
from prompt_toolkit.layout.controls import TokenListControl
from prompt_toolkit.layout.containers import ConditionalContainer, \
    ScrollOffsets, HSplit
from prompt_toolkit.layout.dimension import LayoutDimension as D
from prompt_toolkit.mouse_events import MouseEventTypes
from prompt_toolkit.token import Token
from prompt_toolkit.styles import style_from_dict

from .. import PromptParameterException


# custom control based on TokenListControl


def if_mousedown(handler):
    def handle_if_mouse_down(cli, mouse_event):
        if mouse_event.event_type == MouseEventTypes.MOUSE_DOWN:
            return handler(cli, mouse_event)
        else:
            return NotImplemented

    return handle_if_mouse_down


class InquirerControl(TokenListControl):
    pointer_index = 0
    selected_options = []  # list of names
    answered = False
    choices = []  # list (name, value)

    def __init__(self, choices, **kwargs):
        self._init_choices(choices)
        super(InquirerControl, self).__init__(self._get_choice_tokens,
                                              **kwargs)

    def _init_choices(self, choices):
        # helper to convert from question format to internal format
        for c in choices:
            if 'value' in c:
                self.choices.append((c['name'], c['value']))
            else:
                self.choices.append((c['name'], c['name']))
            if 'checked' in c and c['checked']:
                self.selected_options.append(c['name'])

    @property
    def choice_count(self):
        return len(self.choices)

    def _get_choice_tokens(self, cli):
        tokens = []
        T = Token

        def append(index, label):
            selected = label in self.selected_options
            pointed_at = (index == self.pointer_index)

            @if_mousedown
            def select_item(cli, mouse_event):
                # bind option with this index to mouse event
                if label in self.selected_options:
                    self.selected_options.remove(label)
                else:
                    self.selected_options.append(label)
                #self.selected_option_index = index
                #self.answered = True
                #cli.set_return_value(None)

            #token = T.Selected if selected else T

            if pointed_at:
                tokens.append((T.Pointer, ' \u276f', select_item))  # ' >'
            else:
                tokens.append((T, '  ', select_item))
            if selected:
                #tokens.append((T, '\u25c9 '))  # 'o ' - FISHEYE
                tokens.append((T, '\u25cf ', select_item))  # 'o ' - FISHEYE
            else:
                tokens.append((T, '\u25cb ', select_item))  # 'o ' - FISHEYE

            if pointed_at:
                tokens.append((Token.SetCursorPosition, ''))

            tokens.append((T.Selected if selected else T, label, select_item))
            tokens.append((T, '\n'))

        # prepare the select choices
        for i, choice in enumerate(self.choices):
            append(i, choice[0])
        tokens.pop()  # Remove last newline.
        return tokens

    def get_selected_values(self):
        # get values not labels
        return [c[0] for c in self.choices if c[0] in self.selected_options]

    @property
    def line_count(self):
        return len(self.choices)


def question(message, **kwargs):
    # TODO add bottom-bar (Move up and down to reveal more choices)
    # TODO extract common parts for list, checkbox, rawlist, expand
    # TODO disabled
    if not 'choices' in kwargs:
        raise PromptParameterException('choices')
    # this does not implement default, use checked...
    if 'default' in kwargs:
        raise ValueError('Checkbox does not implement \'default\' '
                         'use \'checked\':True\' in choice!')

    choices = kwargs.pop('choices', None)
    default = kwargs.pop('default', 0)  # TODO

    # TODO style defaults on detail level
    style = kwargs.pop('style', style_from_dict({
        Token.QuestionMark: '#5F819D',
        Token.Selected: '',  # default
        Token.Pointer: '#FF9D00 bold',  # AWS orange
        Token.Instruction: '',  # default
        Token.Answer: '#FF9D00 bold',  # AWS orange
        Token.Question: 'bold',
    }))

    ic = InquirerControl(choices)

    def get_prompt_tokens(cli):
        tokens = []
        T = Token

        tokens.append((Token.QuestionMark, '?'))
        tokens.append((Token.Question, ' %s ' % message))
        if ic.answered:
            #pass
            tokens.append((Token.Answer, ' done'))
        else:
            tokens.append((Token.Instruction,
                           ' (<up>, <down> to move, <space> to select, <a> '
                           'to toggle, <i> to invert)'))
        return tokens

    # assemble layout
    layout = HSplit([
        Window(height=D.exact(1),
               content=TokenListControl(get_prompt_tokens, align_center=False)),
        ConditionalContainer(
            Window(
                ic,
                width=D.exact(43),
                height=D(min=3),
                scroll_offsets=ScrollOffsets(top=1, bottom=1)
            ),
            filter=~IsDone()
        )
    ])

    # key bindings
    manager = KeyBindingManager.for_prompt()

    @manager.registry.add_binding(Keys.ControlQ, eager=True)
    @manager.registry.add_binding(Keys.ControlC, eager=True)
    def _(event):
        raise KeyboardInterrupt()
        # event.cli.set_return_value(None)

    @manager.registry.add_binding(' ', eager=True)
    def toggle(event):
        pointed_choice = ic.choices[ic.pointer_index][0]  # name
        if pointed_choice in ic.selected_options:
            ic.selected_options.remove(pointed_choice)
        else:
            ic.selected_options.append(pointed_choice)

    @manager.registry.add_binding('i', eager=True)
    def invert(event):
        inverted_selection = [c[0] for c in ic.choices if
                              c[0] not in ic.selected_options]
        ic.selected_options = inverted_selection

    @manager.registry.add_binding('a', eager=True)
    def all(event):
        all_selected = True  # all choices have been selected
        for c in ic.choices:
            if c[0] not in ic.selected_options:
                # add missing ones
                ic.selected_options.append(c[0])
                all_selected = False
        if all_selected:
            ic.selected_options = []

    @manager.registry.add_binding(Keys.Down, eager=True)
    def move_cursor_down(event):
        ic.pointer_index = (
            (ic.pointer_index + 1) % ic.line_count)

    @manager.registry.add_binding(Keys.Up, eager=True)
    def move_cursor_up(event):
        ic.pointer_index = (
            (ic.pointer_index - 1) % ic.line_count)

    @manager.registry.add_binding(Keys.Enter, eager=True)
    def set_answer(event):
        ic.answered = True
        event.cli.set_return_value(ic.get_selected_values())

    return Application(
        layout=layout,
        key_bindings_registry=manager.registry,
        mouse_support=True,
        style=style
    )