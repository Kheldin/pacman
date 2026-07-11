from mazegenerator import MazeGenerator

if __name__ == "__main__":
    maze = MazeGenerator((15, 15))
    maze.generate()
    print(maze)