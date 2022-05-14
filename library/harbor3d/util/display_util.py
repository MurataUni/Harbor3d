import sys
import numpy as np
# try:
#     import pygame
#     from pygame.locals import *
#     from OpenGL.GL import *
#     from OpenGL.GLU import *
# except:
#         pass

def is_available():
    return "pygame" in sys.modules

def translate_matrix(x, y, z):
    return np.array([\
        [1., 0., 0., 0.],\
        [0., 1., 0., 0.],\
        [0., 0., 1., 0.],\
        [x, y, z, 1.]])

def rotate_matrix_x(theta):
    return np.array([\
        [1., 0., 0., 0.],\
        [0., np.cos(theta), np.sin(theta), 0.],\
        [0., -np.sin(theta), np.cos(theta), 0.],\
        [0., 0., 0., 1.]])

def rotate_matrix_y(theta):
    return np.array([\
        [np.cos(theta), 0., -np.sin(theta), 0.],\
        [0., 1., 0., 0.],\
        [np.sin(theta), 0., np.cos(theta), 0.],\
        [0., 0., 0., 1.]])

def draw_dock(dock):
    if dock.ships is None:
        return
    for ship in dock.ships:
        draw_ship(ship)

def draw_ship(ship):
    if not ship.is_visible:
        return
    if ship.keel is None:
        return
    if None != ship.monocoque_shell:
        draw_monocoque_shell(ship)
        return
    if ship.smoothing:
        pass
    else:
        draw_normal_ship(ship)
    
def draw_monocoque_shell(ship):
    ship.monocoque_shell.translate(np.dot(ship.keel.relative_translation, ship.keel.origin_translation))
        
    for triangle in ship.monocoque_shell.triangles:
        draw_triangle(triangle)

def draw_normal_ship(ship):
    former_rib_edges = None
    for rib in ship.ribs:
        former_rib_edges = draw_rib(ship.keel, rib, former_rib_edges)

def init_gl_view(display):
    pass

def quit_display():
    pass

def start_display(dock, translate_vel, translate_matlix_start, rotate_radian_vel=np.pi/180):
    pass

def draw_triangle(triangle):
    pass

def draw_rib(keel, rib, former_rib_edges):
    pass

def draw_beam(rib_edges, former_rib_edges):
    pass

# def init_gl_view(display):
#     glLoadIdentity()
#     gluPerspective(45, (display[0]/display[1]), 0.1, 500)

# def quit_display():
#     pygame.quit()

# def start_display(dock, translate_vel, translate_matlix_start, rotate_radian_vel=np.pi/180):
#     if not is_available():
#         return
    
#     pygame.init()
#     pygame.display.set_caption('Display')

#     display=(800, 800)
#     pygame.display.set_mode(display, DOUBLEBUF|OPENGL)
#     init_gl_view(display)

#     model_view_matrix = np.matrix(np.identity(4), copy=False, dtype='float32')
#     glGetFloatv(GL_MODELVIEW_MATRIX, model_view_matrix)

#     rotate_matlix = np.matrix(np.identity(4), copy=False, dtype='float32')
#     translate_matlix = translate_matlix_start

#     glMultMatrixf(rotate_matlix)
#     glMultMatrixf(translate_matlix)
    
#     clock = pygame.time.Clock()
#     while True:
#         clock.tick(60)
#         for event in pygame.event.get():
#             if event.type == pygame.QUIT:
#                 pygame.quit()
#                 return
#         keys = pygame.key.get_pressed()
#         if len(keys) != 0:
#             if keys[pygame.K_LEFT]:
#                 rotate_matlix = np.dot(rotate_matlix, rotate_matrix_y(-rotate_radian_vel))
#             if keys[pygame.K_RIGHT]:
#                 rotate_matlix = np.dot(rotate_matlix, rotate_matrix_y(rotate_radian_vel))
#             if keys[pygame.K_UP]:
#                 rotate_matlix = np.dot(rotate_matlix, rotate_matrix_x(-rotate_radian_vel))
#             if keys[pygame.K_DOWN]:
#                 rotate_matlix = np.dot(rotate_matlix, rotate_matrix_x(rotate_radian_vel))
#             if keys[pygame.K_g]:
#                 translate_matlix = np.dot(translate_matlix, translate_matrix(0, 0, translate_vel))
#             if keys[pygame.K_t]:
#                 translate_matlix = np.dot(translate_matlix, translate_matrix(0, 0, -translate_vel))
#             if keys[pygame.K_w]:
#                 translate_matlix = np.dot(translate_matlix, translate_matrix(0, translate_vel, 0))
#             if keys[pygame.K_s]:
#                 translate_matlix = np.dot(translate_matlix, translate_matrix(0, -translate_vel, 0))
#             if keys[pygame.K_a]:
#                 translate_matlix = np.dot(translate_matlix, translate_matrix(-translate_vel, 0, 0))
#             if keys[pygame.K_d]:
#                 translate_matlix = np.dot(translate_matlix, translate_matrix(translate_vel, 0, 0))
#             if keys[pygame.K_SPACE]:
#                 rotate_matlix = np.identity(4)
#                 translate_matlix = translate_matlix_start
#             init_gl_view(display)
#             glMultMatrixf(translate_matlix)
#             glMultMatrixf(rotate_matlix)
#         glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
#         draw_dock(dock)
#         pygame.display.flip()

# def draw_triangle(triangle):
#     if triangle.vertex_1 is None or triangle.vertex_2 is None or triangle.vertex_3 is None:
#         return
#     glLineWidth(1)
#     glBegin(GL_LINE_LOOP)
#     glColor3f(0,1,0.5)

#     glVertex3fv((triangle.vertex_1.translated_position[0], 
#         triangle.vertex_1.translated_position[1], 
#         triangle.vertex_1.translated_position[2]))

#     glVertex3fv((triangle.vertex_2.translated_position[0], 
#         triangle.vertex_2.translated_position[1], 
#         triangle.vertex_2.translated_position[2]))
    
#     glVertex3fv((triangle.vertex_3.translated_position[0], 
#         triangle.vertex_3.translated_position[1], 
#         triangle.vertex_3.translated_position[2]))
    
#     glEnd()

# def draw_rib(keel, rib, former_rib_edges):
#     if rib.edges is None or len(rib.edges) == 0:
#         return None
#     glLineWidth(1)
#     glBegin(GL_LINE_STRIP)
#     return_edges = []
#     glColor3f(0,1,0)
#     for edge in rib.edges:
#         translated_edge = np.dot(np.array([edge[0], edge[1], 0., 1.]), keel.translation(rib.position))
#         glVertex3fv((translated_edge[0], translated_edge[1], translated_edge[2]))
#         return_edges.append(translated_edge)
#     glVertex3fv((return_edges[0][0], return_edges[0][1], return_edges[0][2]))
#     glEnd()
#     if former_rib_edges is not None \
#         and len(former_rib_edges) != 0 \
#         and len(return_edges) != 0:
#         draw_beam(return_edges, former_rib_edges)
#     return return_edges

# def draw_beam(rib_edges, former_rib_edges):
#     edge_max = len(rib_edges)
#     if edge_max < len(former_rib_edges):
#         edge_max = len(former_rib_edges)
#     glLineWidth(1)
#     glBegin(GL_LINES)
#     glColor3f(0.5, 0.5, 0)
#     for i in range(edge_max):
#         index_former_rib_edge = i if i < len(former_rib_edges) - 1 else len(former_rib_edges) - 1
#         index_edge = i if i < len(rib_edges) - 1 else len(rib_edges) - 1
#         glVertex3fv((former_rib_edges[index_former_rib_edge][0], former_rib_edges[index_former_rib_edge][1], former_rib_edges[index_former_rib_edge][2]))
#         glVertex3fv((rib_edges[index_edge][0], rib_edges[index_edge][1], rib_edges[index_edge][2]))
#     glEnd()