import open3d as o3d
print('open3d imported', o3d.__version__)
vis = o3d.visualization.Visualizer()
print('visualizer created')
vis.create_window('debug', width=800, height=600)
print('window created')
vis.destroy_window()
