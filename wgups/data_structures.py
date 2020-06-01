from typing import Dict, List, Optional, Tuple, TypeVar

# Custom types representing Keys and Items used in the Hash Table
TKey = TypeVar("TKey")
TItem = TypeVar("TItem")


# This Hash Table uses chaining, or nested lists at each bucket, and
# maintains a size of at least double that of the number of items that occupy it.
# This will ensure optimal time and space complexity for inserts and look-ups
# by minimizing the potential for probing and collisions. Space complexity O(n).
class ChainingHashTable:
    # Constructor with optional parameters for initial capacity and threshold values.
    def __init__(self, initial_capacity: int = 8, initial_threshold: int = 0.5):
        # Initialize table with buckets set to None
        self.__data = initial_capacity * [None]
        self.__occupancy = 0
        self.__occupancy_threshold = initial_threshold

    # Insert a new item associated with a unique key in to the hash table,
    # returns None if a new item was inserted and the old item if an existing item was updated.
    # The space complexity of insertion is O(1) and the time complexity is on average O(1)
    # and O(N) in the worst-case.
    def insert(self, key: TKey, item: TItem) -> Optional[TItem]:
        current_capacity = len(self.__data)
        bucket_index = hash(key) % current_capacity

        # If no item is at this index, start a new list in this bucket with this (key, item)
        # pair as the first item.
        if self.__data[bucket_index] is None:
            self.__data[bucket_index] = [(key, item)]
            self.__occupancy += 1
        # Otherwise we need to see if the key associated with this item is stored in this list
        # and the item needs an update or if we need to add this as a new item.
        elif isinstance(self.__data[bucket_index], list):
            existing_list = self.__data[bucket_index]
            for i, item_tuple in enumerate(existing_list):
                if item_tuple[0] == key:
                    previous_item = item_tuple[1]
                    existing_list[i] = (key, item)
                    return previous_item
            # If we didn't come across the key its a new item, add it to the end, and
            # check if a re-size is needed.
            existing_list.append((key, item))
            self.__occupancy += 1

            if self.__needs_resize_with_insert():
                self.__resize()

            return None

    # Searches for item based on key inserted, returns item or None if not found.
    # The space complexity of search is O(1) and the time complexity is on average O(1)
    # and O(N) in the worst-case.
    def search(self, key: TKey) -> TItem:
        found_item = None
        # Look-up the location of the item based on its key. If a location is found
        # use it to return the item.
        item_location = self.__find_item(key)
        if item_location is not None:
            found_item = self.__data[item_location[0]][item_location[1]][1]

        return found_item

    # Removes for item based on key given, returns item removed or None if not found.
    # The space complexity of remove is O(1) and the time complexity is on average O(1)
    # and O(N) in the worst-case.
    def remove(self, key: TKey) -> TItem:
        item_removed = None
        # Look-up the location of the item based on its key. If a location is found
        # use it to remove the item and reduce the current occupancy count.
        item_location = self.__find_item(key)
        if item_location is not None:
            item_removed = self.__data[item_location[0]][item_location[1]]
            del self.__data[item_location[0]][item_location[1]]
            self.__occupancy -= 1

        return item_removed

    # Provide a quick means for the user to get a list of all keys currently stored
    # in the hash table. The space and time complexities are O(n).
    def keys(self) -> List[TKey]:
        keys = []
        for i in range(len(self.__data)):
            if isinstance(self.__data[i], list):
                for tuple_item in self.__data[i]:
                    keys.append(tuple_item[0])
        return keys

    # Provide a quick means for the user to get a list of all items currently stored
    # in the hash table. The space and time complexities are O(n).
    def values(self) -> List[TItem]:
        items = []
        for i in range(len(self.__data)):
            if isinstance(self.__data[i], list):
                for tuple_item in self.__data[i]:
                    items.append(tuple_item[1])
        return items

    # Method to locate the bucket and the index within the bucket's list where an item
    # is stored. Performs the look-up based on an item's associated key and returns
    # its location as a tuple in the form (bucket_index, list_index).
    def __find_item(self, key: TKey) -> Tuple[int, int]:
        # Calculate the bucket an item with this key would be stored at and set a
        # default value of None to return in case we don't find an item with this key.
        bucket_index = hash(key) % len(self.__data)
        found_item_location = None

        # If a list exists at this bucket and it is not empty iterate through and check
        # for the key. Return the bucket_index and list_index if the key is found.
        if isinstance(self.__data[bucket_index], list):
            found_list = self.__data[bucket_index]
            for (list_index, tuple_item) in enumerate(found_list):
                if tuple_item[0] == key:
                    found_item_location = (bucket_index, list_index)
                    break

        return found_item_location

    # Check to see if the current capacity warrants a re-size, returning a boolean.
    # This constant time operation has a time and space complexity of O(1).
    def __needs_resize_with_insert(self) -> bool:
        return (self.__occupancy + 1 / len(self.__data)) >= self.__occupancy_threshold

    # Resize the size of the existing list to double its current size and
    # copy over each item with a new hash based on the new length.
    # Re-sizing has a time and space complexity of O(n).
    def __resize(self) -> None:
        # Save a reference to the old list and set the table's data property
        # to the new list of None.
        new_length = len(self.__data) * 2
        new_data = new_length * [None]
        old_data = self.__data
        self.__data = new_data

        # If the list at any given index in the old list is not empty,
        # iterate through its items and insert them into our new list with new hashes.
        previous_occupancy = self.__occupancy
        new_data_occupancy = 0
        self.__occupancy = 0
        for nested_list in old_data:
            if nested_list is not None:
                for item_tuple in nested_list:
                    is_new_item = self.insert(item_tuple[0], item_tuple[1])
                    if is_new_item:
                        new_data_occupancy += 1

            # If we have determined every item has been copied over based on
            # our occupancy count we can stop copying.
            if new_data_occupancy == previous_occupancy:
                break

    # Convenience method to set item
    def __setitem__(self, key, item) -> None:
        self.insert(key, item)

    # Convenience method to get item
    def __getitem__(self, key) -> TItem:
        return self.search(key)

    # Convenience method to check for existence of key in table with in
    def __contains__(self, key) -> bool:
        return self.search(key) is not None

    # Convenience method for string representation of hash table
    def __str__(self) -> str:
        return f"[{', '.join(str(tuple_item) for tuple_item in self)}]"

    # Convenience method to get actual occupancy of current table as length
    def __len__(self) -> int:
        return self.__occupancy

    # Convenience method to allow iteration through the items of the hash table
    def __iter__(self) -> Tuple[TKey, TItem]:
        for i in range(len(self.__data)):
            if isinstance(self.__data[i], list):
                for tuple_item in self.__data[i]:
                    yield tuple_item


# Custom types representing Vertices used in the Graph
TVertex = TypeVar("TVertex")


# Adjacency Matrix Graph. A graph represented by an n x n matrix that indicates
# edges between the graph's vertices. Not for use with graph's that will have sparse
# edges. Space complexity O(n^2).
class AMGraph:
    def __init__(self):
        self.__adjacency_matrix = {}

    # To maintain a n x n matrix as each new vertex adds a 'row' we also need to add a new
    # 'column' representing this new vertex to each existing 'row' or vertex.
    # Space complexity O(1) and time complexity O(n).
    def insert_vertex(self, new_vertex: TVertex) -> Optional[TVertex]:
        # If this is an existing vertex we can't reinsert, return None
        if new_vertex in self.__adjacency_matrix:
            return None
        # Set the initial value in the new 'column' to None for each vertex since we don't know
        # if the existing vertex connects to the new vertex by an edge.
        for existing_vertex in self.__adjacency_matrix:
            self.__adjacency_matrix[existing_vertex][new_vertex] = None
        # Add the new vertex in
        self.__adjacency_matrix[new_vertex] = {}
        # Set the 'columns' of the new vertex's 'row' with entries for each existing
        # vertex as None to indicate no known edge between the vertices.
        for existing_vertex in self.__adjacency_matrix:
            self.__adjacency_matrix[new_vertex][existing_vertex] = None

        # Return the vertex after it is successfully inserted into the graph
        return new_vertex

    # Add a directed edge to the graph with an optional weight parameter.
    # Space and time complexity O(1).
    def add_edge(self, from_vertex: TVertex, to_vertex: TVertex, weight: float = 1.0) -> None:
        if from_vertex in self.__adjacency_matrix and to_vertex in self.__adjacency_matrix:
            self.__adjacency_matrix[from_vertex][to_vertex] = weight

    # Remove the 'row' corresponding to the vertex being removed and
    # every other vertices 'column' associated with it.
    # Space and time complexity O(1).
    def remove_vertex(self, vertex: TVertex) -> Optional[TVertex]:
        # If the vertex is not in the list return None
        if vertex not in self.__adjacency_matrix:
            return None

        # Remove vertex
        del self.__adjacency_matrix[vertex]
        for vertex_row in self.__adjacency_matrix:
            del self.__adjacency_matrix[vertex_row][vertex]

        # After the vertex is removed return it
        return vertex

    # Remove a directed edge associated with two vertices - in one direction.
    # Space and time complexity O(1).
    def remove_edge(self, from_vertex: TVertex, to_vertex: TVertex) -> None:
        if from_vertex in self.__adjacency_matrix and to_vertex in self.__adjacency_matrix:
            self.__adjacency_matrix[from_vertex][to_vertex] = None

    # Convenience method to get the matrix row for a vertex
    def __getitem__(self, vertex) -> Dict[TVertex, Dict]:
        return self.__adjacency_matrix[vertex]

    # Convenience method to check the matrix for a vertex
    def __contains__(self, vertex) -> bool:
        return vertex in self.__adjacency_matrix

    # Convenience method to return the graph as to a string
    def __str__(self) -> str:
        matrix_str = ""
        for vertex, adjacent_vertices in self.__adjacency_matrix.items():
            matrix_str += f"{vertex}: {adjacent_vertices}\n"
        return matrix_str

    # Convenience method to get number of vertices in matrix
    def __len__(self) -> int:
        return len(self.__adjacency_matrix)

    # Convenience method to allow iteration through the items of the matrix
    def __iter__(self):
        for vertex, adjacent_vertices in self.__adjacency_matrix.items():
            yield vertex, adjacent_vertices


