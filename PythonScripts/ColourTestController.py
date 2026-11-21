from Controller import Controller
from RGB import RGB
from SettingsController import SettingsController
from CircularStack import CircularStack
import uuid


class ColourTestController(Controller):

    ### INITIALISATION
    ## Set up working colours, settings, and history
    def __init__(self, name: str):
        super().__init__(name)

        # working colours
        self.colour1 = RGB(255, 0, 0)
        self.colour2 = RGB(0, 255, 0)
        self.colour3 = RGB(0, 0, 255)

        # convergence multiplier controls how fast S shrinks
        self.convergance_multiplyer = 1.0

        # ratio state (start with pure R,G,B)
        self.ratios = [
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1]
        ]

        # spread S controls intensity of colours
        self.S = 80  # starting spread

        # track current background (starts white)
        self.current_background = RGB(255, 255, 255)

        # circular history of full states
        self.previous_colours = CircularStack()

        # settings controller
        self.settings = SettingsController(name)

        # NOTE:
        # SettingsController __init__ now ENSURES "themes" exists and is well-formed,
        # so we DO NOT touch self.settings._preferences["themes"] here anymore.

        # snapshot initial state (white background)
        self.previous_colours.push(
            self._snapshot_state(self.current_background)
        )

    ### SNAPSHOT STATE
    ## Create a full copy of the current colour state INCLUDING background
    def _snapshot_state(self, background: RGB) -> dict:
        return {
            "colour1": [self.colour1.r, self.colour1.g, self.colour1.b],
            "colour2": [self.colour2.r, self.colour2.g, self.colour2.b],
            "colour3": [self.colour3.r, self.colour3.g, self.colour3.b],
            "background": [background.r, background.g, background.b]
        }

    ### RESTORE STATE
    ## Restore colours from a snapshot
    def _restore_state(self, state: dict) -> None:
        self.colour1 = RGB(*state["colour1"])
        self.colour2 = RGB(*state["colour2"])
        self.colour3 = RGB(*state["colour3"])
        self.current_background = RGB(*state["background"])

    ### GET COLOURS
    ## Return current working colours as RGB objects
    def get_colours(self) -> list[RGB]:
        return [self.colour1, self.colour2, self.colour3]

    ### GET COLOURS AS LISTS
    ## Return current colours as [[r,g,b], ...] for C#
    def get_colours_as_lists(self) -> list[list[int]]:
        return [[c.r, c.g, c.b] for c in self.get_colours()]

    ### GENERATE NEW COLOURS
    ## Ratio evolution algorithm with midpoint scaling and converging spread
    def get_new_colours(self, button_no) -> list[list[int]]:
        # Save previous state for undo/history
        self.previous_colours.push(self._snapshot_state(self.current_background))

        # Get selected ratio
        selected_ratio = self.ratios[button_no]

        # Update background to selected colour
        selected_colour = self.get_colours()[button_no]
        self.current_background = RGB(selected_colour.r, selected_colour.g, selected_colour.b)

        # Generate next 3 ratios by adding 1 to each channel
        R, G, B = selected_ratio
        new_ratios = [
            [R + 1, G,     B    ],
            [R,     G + 1, B    ],
            [R,     G,     B + 1]
        ]
        self.ratios = new_ratios

        # Spread behaviour: grow slightly, then shrink
        self.S += 10                                  # exploration
        self.S *= (1 - 0.1 * self.convergance_multiplyer)  # convergence
        self.S = max(10, min(self.S, 120))            # clamp

        # Convert ratios → RGB around midpoint
        M = 128  # midpoint
        new_colours = []

        for ratio in new_ratios:
            r_ratio, g_ratio, b_ratio = ratio
            avg = (r_ratio + g_ratio + b_ratio) / 3

            R_val = int(M + self.S * (r_ratio - avg))
            G_val = int(M + self.S * (g_ratio - avg))
            B_val = int(M + self.S * (b_ratio - avg))

            colour = RGB(R_val, G_val, B_val)
            colour.dampen()
            new_colours.append(colour)

        # Update internal state
        for i, col in enumerate(new_colours):
            self.set_colour(col, i)

        # Return raw RGB lists for C#
        return [c.get_rgb() for c in new_colours]

    ### SET COLOUR
    ## Assign a colour to one of the three slots
    def set_colour(self, colour: RGB, i: int) -> None:
        if i == 0:
            self.colour1 = colour
        elif i == 1:
            self.colour2 = colour
        elif i == 2:
            self.colour3 = colour

    ### BACK BUTTON
    ## Restore the previous full colour state AND background
    def on_back_button(self):
        previous_state = self.previous_colours.pop_new()
        if previous_state is None:
            self.log("Back button pressed but no previous state available.")
            return None

        self._restore_state(previous_state)
        self.log("Reverted colours to previous state.")

        return {
            "colours": self.get_colours_as_lists(),
            "background": previous_state["background"]
        }

    ### SAVE PREFERRED COLOUR
    ## Save final chosen colour as theme (primary, background, accent) and generate XAML theme file
    def save_prefered_colour(self) -> None:
        # final chosen colour
        primary = self.current_background

        # generate lighter and darker variants
        background = self.lighten(primary, 0.35)
        accent = self.darken(primary, 0.35)

        # generate a unique theme name
        theme_name = f"Theme_{uuid.uuid4().hex[:6]}"

        # helper
        def to_hex(rgb: RGB) -> str:
            return f"#{rgb.r:02X}{rgb.g:02X}{rgb.b:02X}"

        primary_hex = to_hex(primary)
        background_hex = to_hex(background)
        accent_hex = to_hex(accent)

        # FULL WPF‑COMPATIBLE THEME FILE
        xaml_content = f"""
<ResourceDictionary xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
                    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">

    <!-- Global brushes -->
    <SolidColorBrush x:Key="WindowBackground" Color="{background_hex}"/>
    <SolidColorBrush x:Key="PrimaryColor"    Color="{primary_hex}"/>
    <SolidColorBrush x:Key="AccentColor"     Color="{accent_hex}"/>

    <!-- Default Button style -->
    <Style TargetType="Button">
        <Setter Property="Background" Value="{{DynamicResource AccentColor}}"/>
        <Setter Property="Foreground" Value="White"/>
        <Setter Property="BorderThickness" Value="0"/>
        <Setter Property="Padding" Value="8,4"/>
        <Setter Property="Cursor" Value="Hand"/>
        <Setter Property="Template">
            <Setter.Value>
                <ControlTemplate TargetType="Button">
                    <Border Background="{{TemplateBinding Background}}"
                            CornerRadius="4">
                        <ContentPresenter HorizontalAlignment="Center"
                                          VerticalAlignment="Center"/>
                    </Border>
                </ControlTemplate>
            </Setter.Value>
        </Setter>
    </Style>

</ResourceDictionary>
""".strip()

        # save XAML file
        self.settings.save_theme_xaml(f"{theme_name}.xaml", xaml_content)

        # register theme name in settings ("themes" holds options + current)
        self.settings.add_option("themes", theme_name)

        # set current theme IN THE SAME SETTING
        self.settings.set_current("themes", theme_name)

        self.log(f"Saved preferred theme: {theme_name}")

    def lighten(self, rgb: RGB, amount: float) -> RGB:
        return RGB(
            min(255, int(rgb.r + (255 - rgb.r) * amount)),
            min(255, int(rgb.g + (255 - rgb.g) * amount)),
            min(255, int(rgb.b + (255 - rgb.b) * amount))
        )

    def darken(self, rgb: RGB, amount: float) -> RGB:
        return RGB(
            max(0, int(rgb.r * (1 - amount))),
            max(0, int(rgb.g * (1 - amount))),
            max(0, int(rgb.b * (1 - amount)))
        )

    ### RESET TEST
    ## Reinitialise controller
    def reset_test(self) -> None:
        self.__init__(self.name)