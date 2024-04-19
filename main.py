import matplotlib.pyplot as plt
import numpy as np
import math
from matplotlib.patches import Polygon
from typing import List
from copy import deepcopy


A = np.array([[np.cos(np.radians(30)), np.sin(np.radians(30))], [0, -1]]).T
    
def convert_skewed_to_cartesian(A, x):
    # so (1,0) in skewed is (cos(30), sin(30)) in cartesian  (np.sqrt(3)/2, 0.5)
    # and (0,1) in skewed is (-1, 0) in cartesian (this is cos(270), sin(270))
    return 2 * A @ np.array(x)
    
def convert_cartesian_to_skewed(A, x):
    return 0.5 * np.linalg.inv(A) @ np.array(x)

def rotate_in_cartesian(x, alpha):
    # if we go counter-clockwise
    R = np.array([[np.cos(np.radians(alpha)), -np.sin(np.radians(alpha))], [np.sin(np.radians(alpha)), np.cos(np.radians(alpha))]])
    return R @ x


class Hex:

    def __init__(self, d1, d2, color=None):
        # we are defining the hexagon in skewed coordinates d1, d2, 
        # d1 and d2 are at 120 degrees angle from each other
        
        N = 5
        self.d1 = d1
        self.d2 = d2
        self.color = color
        self.index = d2*(N) + d1
        angles = np.linspace(0, 2*np.pi, 7)
        # Calculate the x and y coordinates of the hexagon vertices
        x = np.cos(angles)
        y = np.sin(angles)
        self.xy = list(zip(x, y)) + 2*d1*self._translate_distance(30) + 2*d2*self._translate_distance(270)
        self.polygon = Polygon(self.xy, closed=True, edgecolor='black', facecolor=color)
        self.xc, self.yc = self.get_polygon_center()
        
    @property
    def coord(self):
        return (self.d1, self.d2)
    
    def get_xy_of_a_point_at_angle(self, angle):
        radians = np.radians(angle)
        return np.array([np.cos(radians), np.sin(radians)])

    def _translate_distance(self, angle):
        """angle can be 30, 90, 150, 210, 270, 330"""
        return (self.get_xy_of_a_point_at_angle(angle+30) + self.get_xy_of_a_point_at_angle(angle-30)) / 2
        
    def get_polygon_center(self):
        x_coords = [point[0] for point in self.xy[:-1]]
        y_coords = [point[1] for point in self.xy[:-1]]
        center_x = np.mean(x_coords)
        center_y = np.mean(y_coords)
        return (center_x, center_y)


class Piece:
    
    def __init__(self, name, color, index, locations):
        # for example: ('bone', 0, hexagones=[(0,0), (0,1), (1,1), (2,1), (2,2)])
        """hexagons must start with (0,0), as this will determine the position of the piece on the board
        piece will be defined on the board by i,j where 0,0 piece is, as well as angle of rotation.
        so for example we will have solution like: [['post', location=23, angle=120], ...]
        """
        self.name = name
        self.color = color
        self.index = index
        self.locations = locations
        
    @property
    def hexagons(self):
        return [Hex(loc[0], loc[1], self.color) for loc in self.locations]


def translate(piece, d, color=None):
    dx, dy = d 
    return Piece(piece.name, piece.color if not color else color, piece.index, [(x+dx, y+dy) for x, y in piece.locations])


def rotate(piece, angle, color=None):
    """rotate the piece by angle degrees (angle can be only 0, 60, 120, 180, 240, 300)
    we always do the rotation relative to the center of mass of the piece
    """
    if angle not in {0, 60, 120, 180, 240, 300}:
        raise ValueError("angle must be 0, 60, 120, 180, 240 or 300")

    rotated = []
    for loc in piece.locations:
        a = convert_skewed_to_cartesian(A, loc)
        b = rotate_in_cartesian(a, angle)
        c = convert_cartesian_to_skewed(A, b)
        rotated.append(tuple(np.round(c).astype(int)))
    
    return Piece(piece.name, piece.color if not color else color, piece.index, rotated)
    
# def normalize_piece(piece):
#     """not used: translate the piece so that the center of mass is at (0,0)"""   
#     x_norm = int(np.round(np.mean([x for x,y in piece])))
#     y_norm = int(np.round(np.mean([y for x,y in piece])))
    
#     return [(x - x_norm, y - y_norm) for x, y in piece]


class Board:
        
    def __init__(self):
        
        self.points = [
            (0,0), (1, 0), (2,0), (3,0), (4,0),
            (0,1), (1, 1), (2,1), (3,1), (4,1), (5,1),
            (0,2), (1, 2), (2,2), (3,2), (4,2), (5,2), (6,2),
            (0,3), (1, 3), (2,3), (3,3), (4,3), (5,3), (6,3), (7,3),
            (0,4), (1, 4), (2,4), (3,4), (4,4), (5,4), (6,4), (7,4), (8,4),
            (1,5), (2, 5), (3,5), (4,5), (5,5), (6,5), (7,5), (8,5),
            (2,6), (3, 6), (4,6), (5,6), (6,6), (7,6), (8,6),
            (3,7), (4, 7), (5,7), (6,7), (7,7), (8,7),
            (4,8), (5, 8), (6,8), (7,8), (8,8)
        ]
        
        self.occupied = {point: None for point in self.points}
        
    def draw(self):
        fig, ax = plt.subplots(figsize=(6, 4))
        for point in self.points:
            if self.occupied[point] is None:
                h = Hex(*point, color='none')
            else:
                h = Hex(*point, color=self.occupied[point].color)        
            ax.add_patch(h.polygon)
            ax.text(h.xc, h.yc, h.index, ha='center', va='center', color='cyan')
                
        ax.set_aspect('equal')
        ax.set_xlim(-5, 20)
        ax.set_ylim(-15, 5)
        
    def can_add_piece(self, piece: Piece):
        for hexagon in piece.hexagons:
            # out-of-bounds or already occupied
            if hexagon.coord not in self.occupied or \
                self.occupied[hexagon.coord] is not None:   
                return False
        return True
        
    def add_piece(self, piece: Piece):
        """add a piece to the board """
        if not self.can_add_piece(piece):
            return False
        
        for hexagon in piece.hexagons:
            self.occupied[hexagon.coord] = hexagon
        
        return True
    
    def remove_piece(self, piece: Piece):
        for hexagon in piece.hexagons:
            self.occupied[hexagon.coord] = None


def find_min_max(piece: Piece):
    """
    Finds the minimum and maximum x and y coordinates of the piece in cartesian coordinates. Useful for plotting.
    """

    if not isinstance(piece, Piece):
        raise TypeError("piece must be Piece object")
    
    temp = [convert_skewed_to_cartesian(A, np.array(hexagon.coord)) for hexagon in piece.hexagons]
    x_coords = [point[0] for point in temp]
    y_coords = [point[1] for point in temp]
    return min(x_coords), max(x_coords), min(y_coords), max(y_coords)


def draw_pieces(pieces: List[Piece], min_max=None, title=None):
            
    if not isinstance(pieces, list):
        raise TypeError("pieces must be a list of Piece objects")
    
    # Create a figure and axes
    fig, ax = plt.subplots()
    xmin = math.inf
    xmax = -math.inf
    ymin = math.inf
    ymax = -math.inf
    
    for piece in pieces:
        xminp, xmaxp, yminp, ymaxp = find_min_max(piece)
        xmin = min(xmin, xminp)
        xmax = max(xmax, xmaxp)
        ymin = min(ymin, yminp)
        ymax = max(ymax, ymaxp)
        
        # draw hex by hex
        for h in piece.hexagons:
            ax.add_patch(h.polygon)
            ax.text(h.xc, h.yc, h.index, ha='center', va='center', color='cyan')
        
    # Set the aspect ratio to equal
    ax.set_aspect('equal')
    
    if min_max:
        xmin, xmax, ymin, ymax = min_max
    
    if title:
        ax.set_title(title)
    
    ax.set_xlim(xmin - 3, xmax + 3)
    ax.set_ylim(ymin - 3, ymax + 3)
    