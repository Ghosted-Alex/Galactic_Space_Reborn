"""Decorators module"""

import pygame

def button(text, width=560, height=72, order=0):
    """Marks a function as a menu button callback."""
    def decorator(func):
        func._is_menu_button = True
        func._button_text = text
        func._button_width = width
        func._button_height = height
        func._button_order = order
        return func
    return decorator

def submenu(trigger_button_text):
    """Marks a method as an overlay submenu input handler."""
    def decorator(func):
        func._is_submenu_handler = True
        func._trigger_text = trigger_button_text
        return func
    return decorator


def option_def(key, label, choices, order=0, description=""):
    """Declare a persistent, selectable setting on an OptionMenuScene method.

    The decorated method receives the newly selected value after it is saved.
    """
    def decorator(func):
        func._is_option_definition = True
        func._option_key = key
        func._option_label = label
        func._option_choices = tuple(choices)
        func._option_order = order
        func._option_description = description
        return func
    return decorator
