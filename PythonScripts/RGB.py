class RGB:
    def __init__(self, r: int, g: int, b: int):
        self.r = int(r)
        self.g = int(g)
        self.b = int(b)

    # --- Red channel ---
    def get_red(self) -> int:
        return self.r

    def set_red(self, num: int) -> None:
        self.r = int(num)

    def inc_red(self, num: int) -> None:
        self.r += int(num)

    # --- Green channel ---
    def get_green(self) -> int:
        return self.g

    def set_green(self, num: int) -> None:
        self.g = int(num)

    def inc_green(self, num: int) -> None:
        self.g += int(num)

    # --- Blue channel ---
    def get_blue(self) -> int:
        return self.b

    def set_blue(self, num: int) -> None:
        self.b = int(num)

    def inc_blue(self, num: int) -> None:
        self.b += int(num)

    # --- Whole colour ---
    def get_rgb(self) -> list[int]:
        return [self.r, self.g, self.b]

    def set_rgb(self, r: int, g: int, b: int) -> None:
        self.r, self.g, self.b = int(r), int(g), int(b)

    def inc_rgb(self, rgb: "RGB") -> "RGB":
        self.r += rgb.r
        self.g += rgb.g
        self.b += rgb.b
        return self

    def max(self) -> int:
        return max(self.r, self.g, self.b)
    
    def min(self) -> int:
        return min(self.r, self.g, self.b)
    
    def dec_rgb(self, rgb: "RGB") -> None:
        self.r -= rgb.r
        self.g -= rgb.g
        self.b -= rgb.b

    def mult_rgb(self, multiplier: float) -> None:
        self.r = int(self.r * multiplier)
        self.g = int(self.g * multiplier)
        self.b = int(self.b * multiplier)

    def dampen(self) -> None:
        # clamp values into valid RGB range [0, 255]
        self.r = max(0, min(255, int(self.r)))
        self.g = max(0, min(255, int(self.g)))
        self.b = max(0, min(255, int(self.b)))

    def inc_bright(self, num: int) -> None:
        self.r += int(num)
        self.g += int(num)
        self.b += int(num)
        
    
    def __repr__(self) -> str:
        return f"RGB({self.r}, {self.g}, {self.b})"
    
    def __add__ (self, other: "RGB") -> "RGB":
        return RGB(self.r + other.r, self.g + other.g, self.b + other.b)
    def __sub__ (self, other: "RGB") -> "RGB":
        return self + other*-1
    def __mul__ (self, scalar: float) -> "RGB":
        return RGB(int(self.r * scalar), int(self.g * scalar), int(self.b * scalar))
    def __truediv__ (self, scalar: float) -> "RGB":
        return self * (1/scalar)