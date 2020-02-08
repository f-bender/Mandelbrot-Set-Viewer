import numpy

class Colormap:
    def __init__(self,nodes, cyclic = False):
        if len(nodes) < 2:
            raise ValueError("Colormap must have at least 2 nodes")
        self.nodes = nodes
        self.cyclic = cyclic
        # complete the cycle if it isn't a complete cycle already
        if cyclic and nodes[-1] != nodes[0]:
            self.nodes.append(nodes[0])

    def get_color(self,map_value):
        if map_value < 0:
            return (0,0,0)
        if not self.cyclic and (map_value > 1 or map_value < 0):
            raise ValueError("map_value parameter of get_color function has to be between 0 and 1 for a non-cyclic Colormap")
        map_value = map_value % 1

        section_nr, dist_in_section = divmod(map_value, 1/(len(self.nodes)-1))
        dist_in_section_normalized = dist_in_section*(len(self.nodes)-1)

        # just adding scaled versions of both neighboring nodes
        return tuple(map(sum,zip( tuple(x*(1-dist_in_section_normalized) for x in self.nodes[int(section_nr)]) , tuple(x*dist_in_section_normalized for x in self.nodes[int(section_nr)+1]) )))


# seemingly unsuccessful attempt at making a colormap with a more performant get_color() method

# class Colormap:
#     def __init__(self,nodes):
#         if len(nodes) < 2:
#             raise ValueError("Colormap must have at least 2 nodes")
#         if any(any(value != 0 and value != 255 for value in node) for node in nodes):
#             raise ValueError("Only primary colors allowed (only r,g,b values of 0 or 255)")
#         self.nodes = nodes
#         self.path_length = 255*(len(nodes)-1)
#         self.directions = tuple(numpy.sign(numpy.subtract(nodes[i+1],nodes[i])) for i in range(len(nodes)-1))

#     def get_color(self,map_value):
#         section_nr, dist_in_section = divmod(int((map_value % 1) * self.path_length), 255)
#         return numpy.add(self.nodes[section_nr],self.directions[section_nr]*dist_in_section)