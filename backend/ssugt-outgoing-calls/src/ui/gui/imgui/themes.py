from imgui_bundle import imgui as im_gui, ImVec2, ImVec4
from imgui_bundle._imgui_bundle.imgui import Col_, Style


def set_style_color(
    style: Style, idx: Col_, r: float, g: float, b: float, a: float
) -> None:
    style.set_color_(idx.value, ImVec4(r, g, b, a))


def set_soft_light_theme():
    ctx = im_gui.get_current_context()
    if ctx is None:
        im_gui.create_context()

    style = im_gui.get_style()

    style.window_padding = ImVec2(15, 15)
    style.window_rounding = 10.0
    style.child_rounding = 6.0
    style.frame_padding = ImVec2(8, 7)
    style.frame_rounding = 8.0
    style.item_spacing = ImVec2(8, 8)
    style.item_inner_spacing = ImVec2(10, 6)
    style.indent_spacing = 25.0
    style.scrollbar_size = 13.0
    style.scrollbar_rounding = 12.0
    style.grab_min_size = 10.0
    style.grab_rounding = 6.0
    style.popup_rounding = 8.0
    style.window_title_align = ImVec2(0.5, 0.5)
    style.button_text_align = ImVec2(0.5, 0.5)
    style.cell_padding = ImVec2(6, 4)

    set_style_color(style, Col_.table_header_bg, 0.85, 0.85, 0.85, 1.00)
    set_style_color(style, Col_.table_border_light, 0.80, 0.80, 0.80, 1.00)
    set_style_color(style, Col_.table_border_strong, 0.70, 0.70, 0.70, 1.00)
    set_style_color(style, Col_.table_row_bg, 0.95, 0.95, 0.95, 1.00)
    set_style_color(style, Col_.table_row_bg_alt, 0.92, 0.92, 0.92, 1.00)
    set_style_color(style, Col_.text, 0.10, 0.10, 0.10, 1.00)
    set_style_color(style, Col_.text_disabled, 0.60, 0.60, 0.60, 1.00)
    set_style_color(style, Col_.window_bg, 0.95, 0.95, 0.95, 1.00)
    set_style_color(style, Col_.child_bg, 0.90, 0.90, 0.90, 1.00)
    set_style_color(style, Col_.popup_bg, 0.95, 0.95, 0.95, 1.00)
    set_style_color(style, Col_.border, 0.80, 0.80, 0.80, 1.00)
    set_style_color(style, Col_.border_shadow, 0.00, 0.00, 0.00, 0.00)
    set_style_color(style, Col_.frame_bg, 0.85, 0.85, 0.85, 1.00)
    set_style_color(style, Col_.frame_bg_hovered, 0.75, 0.75, 0.75, 1.00)
    set_style_color(style, Col_.frame_bg_active, 0.65, 0.65, 0.65, 1.00)
    set_style_color(style, Col_.title_bg, 0.80, 0.80, 0.80, 1.00)
    set_style_color(style, Col_.title_bg_collapsed, 0.70, 0.70, 0.70, 1.00)
    set_style_color(style, Col_.title_bg_active, 0.75, 0.75, 0.75, 1.00)
    set_style_color(style, Col_.menu_bar_bg, 0.85, 0.85, 0.85, 1.00)
    set_style_color(style, Col_.scrollbar_bg, 0.90, 0.90, 0.90, 1.00)
    set_style_color(style, Col_.scrollbar_grab, 0.75, 0.75, 0.75, 1.00)
    set_style_color(style, Col_.scrollbar_grab_hovered, 0.65, 0.65, 0.65, 1.00)
    set_style_color(style, Col_.scrollbar_grab_active, 0.55, 0.55, 0.55, 1.00)
    set_style_color(style, Col_.check_mark, 0.35, 0.35, 0.35, 1.00)
    set_style_color(style, Col_.slider_grab, 0.45, 0.45, 0.45, 1.00)
    set_style_color(style, Col_.slider_grab_active, 0.55, 0.55, 0.55, 1.00)
    set_style_color(style, Col_.button, 0.80, 0.80, 0.80, 1.00)
    set_style_color(style, Col_.button_hovered, 0.70, 0.70, 0.70, 1.00)
    set_style_color(style, Col_.button_active, 0.60, 0.60, 0.60, 1.00)
    set_style_color(style, Col_.header, 0.85, 0.85, 0.85, 1.00)
    set_style_color(style, Col_.header_hovered, 0.75, 0.75, 0.75, 1.00)
    set_style_color(style, Col_.header_active, 0.65, 0.65, 0.65, 1.00)
    set_style_color(style, Col_.separator, 0.80, 0.80, 0.80, 1.00)
    set_style_color(style, Col_.separator_hovered, 0.70, 0.70, 0.70, 1.00)
    set_style_color(style, Col_.separator_active, 0.60, 0.60, 0.60, 1.00)
    set_style_color(style, Col_.resize_grip, 0.85, 0.85, 0.85, 1.00)
    set_style_color(style, Col_.resize_grip_hovered, 0.75, 0.75, 0.75, 1.00)
    set_style_color(style, Col_.resize_grip_active, 0.65, 0.65, 0.65, 1.00)
    set_style_color(style, Col_.plot_lines, 0.40, 0.40, 0.40, 1.00)
    set_style_color(style, Col_.plot_lines_hovered, 0.30, 0.30, 0.30, 1.00)
    set_style_color(style, Col_.plot_histogram, 0.40, 0.40, 0.40, 1.00)
    set_style_color(style, Col_.plot_histogram_hovered, 0.30, 0.30, 0.30, 1.00)
    set_style_color(style, Col_.text_selected_bg, 0.75, 0.75, 0.75, 1.00)
    set_style_color(style, Col_.modal_window_dim_bg, 0.85, 0.85, 0.85, 0.80)
    set_style_color(style, Col_.tab, 0.85, 0.85, 0.85, 1.00)
    set_style_color(style, Col_.tab_hovered, 0.75, 0.75, 0.75, 1.00)
    set_style_color(style, Col_.tab_selected, 0.65, 0.65, 0.65, 1.00)
