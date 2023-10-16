# -*- coding: utf-8 -*-
"""
Created on Fri Aug 08  10:50:32 2023

@author: Zishan Naveed
"""

import re
import math

def extract_node_coordinates(content):
    """
    Extracts node coordinates from the input content.
    Args:
        content (str): The content of the input file.
    Returns:
        list: List of tuples containing node data (node_number, x, y, z).
    """
    # Find the *NODE section and extract the node lines
    node_section = re.search(r"\*NODE\s*([\s\S]*?)(\*\w+|$)", content)
    if not node_section:
        return []

    node_lines = node_section.group(1).strip().split('\n')

    # Extract node number, x, y, and z coordinates from each line
    nodes_data = []
    for line in node_lines:
        parts = line.split()
        try:
            node_number = int(parts[0])
            x, y, z = map(float, parts[1:4])
            nodes_data.append((node_number, x, y, z))
        except ValueError:
            # Skip the line with invalid data and continue processing
			# As file created or saved in LS-Prepost started with '$#'
            continue

    return nodes_data

def transform_nodes(nodes_data, angle_degrees, axis_of_rotation):
    """
    Transforms nodes' coordinates based on rotation angle and axis.
    Args:
        nodes_data (list): List of tuples containing node data (node_number, x, y, z).
        angle_degrees (float): Angle of rotation in degrees.
        axis_of_rotation (str): Axis of rotation ('x', 'y', or 'z').
    Returns:
        list: List of tuples containing Transformed nodes data (node_number, x, y, z).
    """
    angle_rad = math.radians(angle_degrees)
    transformed_nodes = []

    for node_data in nodes_data:
        node_number, x, y, z = node_data

        # Perform rotation based on the specified axis
        if axis_of_rotation == "x":
            # Rotate around the x-axis while keeping x unchanged
            new_y = y * math.cos(angle_rad) - z * math.sin(angle_rad)
            new_z = y * math.sin(angle_rad) + z * math.cos(angle_rad)
            new_x = x
        elif axis_of_rotation == "y":
            # Rotate around the y-axis while keeping y unchanged
            new_x = x * math.cos(angle_rad) + z * math.sin(angle_rad)
            new_z = -x * math.sin(angle_rad) + z * math.cos(angle_rad)
            new_y = y
        elif axis_of_rotation == "z":
            # Rotate around the z-axis while keeping z unchanged
            new_x = x * math.cos(angle_rad) - y * math.sin(angle_rad)
            new_y = x * math.sin(angle_rad) + y * math.cos(angle_rad)
            new_z = z
        else:
            raise ValueError("Invalid axis_of_rotation. Use 'x', 'y', or 'z'.")

        transformed_nodes.append((node_number, new_x, new_y, new_z))

    return transformed_nodes

def update_node_numbers(transformed_nodes, max_node_number):
    """
    Updates node numbers for transformed nodes.
    Args:
        transformed_nodes (list): Transformed nodes data.
        max_node_number (int): Maximum node number in existing nodes.
    Returns:
        list: Transformed nodes data with updated node numbers.
    """
    updated_transformed_nodes = []
    for i, (node_number, x, y, z) in enumerate(transformed_nodes):
        new_node_number = max_node_number + i + 1
        updated_transformed_nodes.append((new_node_number, x, y, z))
    return updated_transformed_nodes

def merge_nodes(original_nodes, transformed_nodes):
    """
    Merges original nodes with transformed nodes.
    Args:
        original_nodes (list): Original nodes data.
        transformed_nodes (list): Transformed nodes' data.
    Returns:
        list: Merged nodes data.
    """
    merged_nodes = original_nodes + transformed_nodes
    merged_nodes.sort(key=lambda x: x[0])
    return merged_nodes
	
def patches_transformed_nodes(original_nodes_data, angles, axis_of_rotation):
    """
    Generate the transformed nodes for different angles and return the keyword string for nodes.
    Args:
        original_nodes_data (list): List of tuples containing original node data (node_number, x, y, z).
        angles (list): List of angles to rotate the nodes.
        axis_of_rotation (str): Axis of rotation ('x', 'y', or 'z').
    Returns:
        str: Keyword string containing the transformed node data.
    """
    merged_nodes = original_nodes_data.copy()  # Initialize merged_nodes with original nodes

    # Loop over the angles and transform the nodes for each angle
    for angle in angles:
        # Transform the nodes
        transformed_nodes = transform_nodes(original_nodes_data, angle, axis_of_rotation)

        # Find the maximum node number in the merged nodes data (or original nodes data if it's the first iteration)
        max_node_number = max(node[0] for node in merged_nodes) if merged_nodes else max(node[0] for node in original_nodes_data)

        # Update the node numbers for the transformed nodes
        updated_transformed_nodes = update_node_numbers(transformed_nodes, max_node_number)

        # Merge original and transformed nodes
        merged_nodes = merge_nodes(merged_nodes, updated_transformed_nodes)

    # Generate the keyword string for nodes
    keywrdNodes = "*NODE\n"
    for node_data in merged_nodes:
        node_num, x, y, z = node_data
        keywrdNodes += str(node_num).rjust(8) + str(round(x, 6)).rjust(15) + str(round(y, 6)).rjust(15) + str(round(z, 6)).rjust(15) + "\n"

    return keywrdNodes

def merge_nurbs_patches(content, angles,inital_nurbs_patches):
    """
    Generate the merged NURBS patches for different angles and return the keyword string for patches.
    Args:
        content (str): Content of the input file.
        angles (list): List of angles to rotate the patches.
        initial NURBS patches (int): orignal part total NURBS patches at inital stage
    Returns:
        str: Keyword string containing the merged NURBS patch data.
    """
    # Use regex to extract the element section
    element_section = re.search(r"\*ELEMENT_SOLID_NURBS_PATCH\n(.*?)(?=\*\w|\Z)", content, re.DOTALL).group(1)
    
    element_section_lines = element_section.strip().split('\n')
    
    # Remove comment lines from element section
    element_section_lines = [line for line in element_section_lines if not line.startswith('$#')]

    keywrdNurbs = "*ELEMENT_SOLID_NURBS_PATCH\n"
	
    patch_id=0
    node_num=0
	
    for i in range(len(angles) + 1):
        tk_end = 0
        nps = 0
        npt = 0
        wf1 = 1
        npr=0
        
        for j in range(inital_nurbs_patches):
            if wf1 == 1:
                block_line = tk_end + ((npr//8)+1)*2 * (nps * npt)
            else:
                block_line = tk_end + (nps * npt)
            
            element_part = element_section_lines[block_line].split()
            element_part2 = element_section_lines[block_line + 1].split()
            npeid, pid, npr, pr, nps, ps, npt, pt = map(int, element_part[0:8])

            wf1, nisr, niss, nist, imass, *other_values = map(int, element_part2[0:8])

            rk = npr + pr + 1
            sk = nps + ps + 1
            tk = npt + pt + 1

            rk_end = (rk + 7) // 8 + (block_line+2)
            sk_end = rk_end + (sk + 7) // 8
            tk_end = sk_end + (tk + 7) // 8
    
            knot_r = [float(num) for line in element_section_lines[(block_line+2):rk_end] for num in line.split()]
            knot_s = [float(num) for line in element_section_lines[rk_end:sk_end] for num in line.split()]
            knot_t = [float(num) for line in element_section_lines[sk_end:tk_end] for num in line.split()]
    
            np_lines = ((npr//8)+1)*nps * npt
            weight_start = tk_end + np_lines
            weight_end = weight_start + np_lines
            
            if wf1 == 1:
                weight_value = []
                for line in element_section_lines[weight_start:weight_end]:
                    values = line.split()
                    #values = values[0:npr]
                    weight_value.extend(map(float, values))
            else:
                weight_value = []
            
            weight_value=[value for value in weight_value if value != 0.0]

            # Write ELEMENT_SOLID_NURBS_PATCH
            keywrdNurbs += str(patch_id + 1).rjust(10) + '1'.rjust(10) + str(npr).rjust(10) + str(pr).rjust(10) + str(nps).rjust(10) + str(ps).rjust(10) + str(npt).rjust(10) + str(pt).rjust(10) + '\n'
            keywrdNurbs += str(wf1).rjust(10) + str(nisr).rjust(10) + str(niss).rjust(10) + str(nist).rjust(10) + "0".rjust(10) + "0".rjust(10) + "0".rjust(10) + "1".rjust(10) + '\n'

            # Write knots in r-direction
            count = 0
            while count < len(knot_r):
                keywrdNurbs += str(round(knot_r[count], 6)).rjust(10)
                count += 1
                if count % 8 == 0:
                    keywrdNurbs += '\n'
            
            if keywrdNurbs[-1] != '\n':
                keywrdNurbs += '\n'
        
            # Write knots in s-direction
            count = 0
            while count < len(knot_s):
                keywrdNurbs += str(round(knot_s[count], 6)).rjust(10)
                count += 1
                if count % 8 == 0:
                    keywrdNurbs += '\n'
            
            if keywrdNurbs[-1] != '\n':
                keywrdNurbs += '\n'
            
            # Write knots in t-direction
            count = 0
            while count < len(knot_t):
                keywrdNurbs += str(round(knot_t[count], 6)).rjust(10)
                count += 1
                if count % 8 == 0:
                    keywrdNurbs += '\n'
                
            if keywrdNurbs[-1] != '\n':
                keywrdNurbs += '\n'
        
            entries_on_line=0
            for k in range(node_num + 1, node_num + (npr * npt * nps) + 1):
                keywrdNurbs += str(k).rjust(10)
                entries_on_line += 1
    
                if entries_on_line == 8:
                    keywrdNurbs += '\n'
                    entries_on_line = 0
        
                if (k - node_num) % npr == 0:
                    keywrdNurbs += '\n'
                    entries_on_line = 0
            for l in range (npr*npt*nps):
                if weight_value:
                    keywrdNurbs += str(weight_value[l]).rjust(10)
                    entries_on_line += 1
                
                else:
                    continue
                    #keywrdNurbs=keywrdNurbs+'0.0'.rjust(10)  # If no weight values, use 0.0
        
                if entries_on_line == 8:
                    keywrdNurbs += '\n'
                    entries_on_line = 0
                
                if ((l+1)%npr ==0):
                    keywrdNurbs += '\n'
                    entries_on_line = 0
            node_num =k
            patch_id +=1
    return keywrdNurbs

if __name__ == "__main__":
    
    original_file_path = "specimen_tension.k"  # File containing the Single Nurbs Patch, created using Splipy Library

    with open(original_file_path, 'r') as file:
        content = file.read()
    
   # angles = [15.65217391,31.30434782,46.95652173,62.60869564,78.26086955,93.91304346,109.5652174,
    #          125.2173913,140.8695652,156.5217391,172.173913,187.8260869,203.4782608,219.1304347,
     #         234.7826087,250.4347826,266.0869565,281.7391304,297.3913043,313.0434782,328.6956521,344.347826]
        angles= [90,180,270]
  # List of angles to rotate the original part]  # List of angles to rotate the original part
    axis_of_rotation = 'y'  # Axis of rotation ('x', 'y', or 'z')
    inital_nurbs_patches = 2

    # Get the nodes of all patches at different angles
    original_nodes_data = extract_node_coordinates(content)
    keywrdNodes = patches_transformed_nodes(original_nodes_data, angles, axis_of_rotation)
    
    # Merge all the patches and update connectivity
    keywrdNurbs = merge_nurbs_patches(content,angles,inital_nurbs_patches)

    # *PART section
    keywrdPart = "*PART\n\n"
    keywrdPart += "1".rjust(10) + "0".rjust(10) + "0".rjust(10) + "0".rjust(10) + "0".rjust(10) + "0".rjust(10) + "0".rjust(10) + "0".rjust(10) + '\n'

    # Combine all the data into a single LS-PrePost file format
    dataDyna = keywrdPart + keywrdNurbs + keywrdNodes + '*END'

    # Write the data into the output file
    with open('full_specimen.k', 'w') as f:
        f.write(dataDyna)