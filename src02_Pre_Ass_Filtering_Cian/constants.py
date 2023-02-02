intensity = 20
sharpness = 0.5


class Box:
    def __init__(self, x1, x2, y1, y2, z1, z2):
        self.x1 = x1
        self.x2 = x2
        self.y1 = y1
        self.y2 = y2
        self.z1 = z1
        self.z2 = z2

        self.intensity = intensity
        self.sharpness = sharpness

    def point_in_box(self, point: list):
        if len(point) != 3:
            print("No valid point")
            return False
        return (self.x1 <= point[0] <= self.x2) and (self.y1 <= point[1] <= self.y2) and (self.z1 <= point[2] <= self.z2)


# this is a method decoding the boxes for any of the ligand size
def get_boxes(denticity, planar: bool = True, input_topology=None, bool_placed_boxes=None):
    """
    planar only important for tetradentates
    """

    box_list = list()
    if input_topology is None:
        if denticity == 1:
            pass
        elif denticity == 2:
            print("retrieving exclusion box for bidentate rotator")
            box_list.append(Box(-100.0, -0.5, -100.0, 100.0, -100.0, 100.0))
            #box_list.append(Box(-5.0, 5.0, -5.0, 5.0, 4.0, 10.0))
            #box_list.append(Box(2.5, 100.0, -5.0, 5.0, -2.5, 5.0))
            #box_list.append(Box(0.4, 100.0, -10.0, 10.0, 0.001, 1000.))
            #box_list.append(Box(-1.0, 1.0, -1.0, 1.0, 0.001, 100.))
        elif denticity == 3:
            box_list.append(Box(0.0, 1.0, -1.0, 1.0, 0.0001, 10.0))
            box_list.append(Box(-1.0, 1.0, -1.0, 1.0, -10.0, -0.2))
            box_list.append(Box(-2.0, 2.0, -2.0, 2.0, 0.8, 10.))
            box_list.append(Box(-6.0, -2.0, -2.0, -1.0, -10.0, 10.0))
            box_list.append(Box(-6.0, -2.0, 1.0, 2.0, -10.0, 10.0))
            box_list.append(Box(-2.0, 2.0, -2.0, 2.0, -10.0, -0.8))
        elif denticity == 5:
            box_list.append(Box(-1.0, 1.0, -1.0, 1.0, 0.3, 2.001))
            box_list.append(Box(-1.8, 1.8, -1.8, 1.8, 2.001, 6.001))
            box_list.append(Box(-4.0, 4.0, -4.0, 4.0, 6.001, 14.001))
        elif denticity == 4 and planar is True:
            box_list.append(Box(-1.0, 1.0, -1.0, 1.0, 0.001, 2.001))
            box_list.append(Box(-1.0, 1.0, -1.0, 1.0, -2.001, -0.001))
            box_list.append(Box(-2.0, 2.0, -2.0, 2.0, -6.001, -2.001))
            box_list.append(Box(-2.0, 2.0, -2.0, 2.0, 2.001, 6.001))
            box_list.append(Box(-4.0, 4.0, -4.0, 4.0, 6.001, 14.001))
            box_list.append(Box(-4.0, 4.0, -4.0, 4.0, -14.001, -6.001))
        elif denticity == 4 and planar is False:
            box_list.append(Box(-10.0, -0.9, -1.8, 1.8, -1.3, 1.3))
            box_list.append(Box(-10.0, -1.8, -5.0, 5.0, -2.0, 2.0))
            box_list.append(Box(-10.0, -3.5, -10.0, 10.0, -10.0, 10.0))
        else:
            pass
    else:
        print("the type of input is: "+str(type(input_topology)))
        print("The input topology is: "+str(input_topology))
        print("we are in the box list section of the code")
        if (denticity == 2) and ((input_topology == [2, 2]) or (input_topology == [2, 1, 1] or input_topology == [2, 1, 0]))and bool_placed_boxes == False:
            # place bidentate in the plane to the right
            print("we are extracting boxes for bidentate ligands 1")
            box_list.append(Box(-4.0, 4.0, -1.4, 1.4, 0.5, 100))  # Top_Plate
            box_list.append(Box(-4.0, 4.0, -1.4, 1.4, -100.0, -0.5))  # Bottom_Plate
            box_list.append(Box(-100, 0.5, -1.4, 1.4, -100.0, 100.0))  # Left_Plate_Big
            box_list.append(Box(-100.0, 100.0, 10.4, 100, -100.0, 100.0))  # Back_Plate
            box_list.append(Box(-100.0, 100.0, -100, -10.4, -100.0, 100.0))  # Front_Plate
            #################################################################
            #box_list.append(Box(-100, 4.0, -8.0, 8.0, 4.0, 5.0))        # +z
            #box_list.append(Box(-100, 4.0, -8.0, 8.0, -5.0, -4.0))      # -z
            #box_list.append(Box(-100, -0.05, -2.0, 2.0, -100, 100.0))    # +x

            #box_list.append(Box(-100, 100, -100, 100, 1.2, 100))        # +z high
            #box_list.append(Box(-100, 100, -100, 100, -100, -1.2))      # -z low
        elif (denticity == 2) and (input_topology == [2, 2]) and bool_placed_boxes == True: # place bidentate in the plane to the left
            print("we are extracting boxes for bidentate ligands 2")
            box_list.append(Box(-4.0, 4.0, -1.4, 1.4, 0.5, 100))  # Top_Plate
            box_list.append(Box(-4.0, 4.0, -1.4, 1.4, -100.0, -0.5))  # Bottom_Plate
            box_list.append(Box(-0.5, 100, -1.4, 1.4, -100.0, 100.0))  # Right_Plate_Big
            box_list.append(Box(-100.0, 100.0, 10.4, 100, -100.0, 100.0))  # Back_Plate
            box_list.append(Box(-100.0, 100.0, -100, -10.4, -100.0, 100.0))  # Front_Plate


            #################################################################
            #box_list.append(Box(-4.0, 100.0, -8.0, 8.0, 4.0, 5.0))    # +z
            #box_list.append(Box(-4.0, 100.0, -8.0, 8.0, -5.0, -4.0))    # -z
            #box_list.append(Box(0.05, 100.0, -2.0, 2.0, -100, 100.0))    # +x

            #box_list.append(Box(-100, 100, -100, 100, 1.2, 100))        # +z high
            #box_list.append(Box(-100, 100, -100, 100, -100, -1.2))      # -z low
        elif (denticity == 2) and (input_topology == [3, 2, 0]):
            positive_y_edge = 0.1
            negative_y_edge = -0.1
            positive_x_frontier = 0.5
            negative_x_frontier = -3.0
            negative_z_frontier = -3.0
            print("we are in the box excluder for the [3,2,0] build process for the bidentate ligand")
            box_list.append(Box(negative_x_frontier, positive_x_frontier, -100.0, negative_y_edge, negative_z_frontier, 1.0))  # Bottom -y
            box_list.append(Box(negative_x_frontier, positive_x_frontier, positive_y_edge, 100.0, negative_z_frontier, 1.0))  # Bottom +y
            box_list.append(Box(0.0, 2.0, -2.0, 2.0, -1.0, 1.0))         #Top Plate



            """
            These were the original boxes for the build process, we can revert back to theses if needed
            box_list.append(Box(-2.0, -1.6, -100.0, -0.5, -5.0, 1.1))   # -x-y
            box_list.append(Box(-2.0, -1.6, 0.5, 100.0, -5.0, 1.1))     # -x+y
            box_list.append(Box(-1.0, 100, -100, 100, -100, 100))       # +x
            """


            pass

    return box_list
