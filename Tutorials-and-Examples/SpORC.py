# Spacecraft Orbit Real-time Chart (SpORC)

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib import cm

def animate_l_mlt(time_hours, L, MLT, color_data=None, 
                  color_label='Electron Density', cmap='plasma',
                  trail_length=50, interval=30, l_range=(1, 7),
                  title='RBSP-A L-MLT Position', save_path=None):
    """
    Animate spacecraft position in L-MLT polar coordinates.
    
    Parameters
    ----------
    time_hours : array-like
        Elapsed time in hours (used for frame stepping).
    L : array-like
        L-shell values (radial coordinate).
    MLT : array-like
        Magnetic Local Time in hours (0–24), mapped to angle.
    color_data : array-like, optional
        Variable to map to marker colour (e.g. density, flux).
    color_label : str
        Label for the colour bar.
    cmap : str
        Matplotlib colourmap name.
    trail_length : int
        Number of past points to show as a fading trail.
    interval : int
        Milliseconds between frames.
    l_range : tuple
        (min, max) for the radial axis.
    title : str
        Plot title.
    save_path : str, optional
        If provided, save animation to this path (.mp4 or .gif).
    
    Returns
    -------
    FuncAnimation object
    """
    # Convert MLT (0-24 hours) to angle in radians
    # Noon (MLT=12) at top, Dawn (MLT=6) on the right, etc.
    theta = (np.pi / 2) - (2 * np.pi * np.array(MLT) / 24.0)
    r = np.array(L)
    
    # Normalise color_data if provided
    if color_data is not None:
        color_data = np.array(color_data)
        c_min, c_max = np.nanmin(color_data), np.nanmax(color_data)
        c_norm = (color_data - c_min) / (c_max - c_min)
        colormap = cm.get_cmap(cmap)
    
    # Set up polar figure
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(8, 8))
    ax.set_theta_zero_location('N')    # Noon at top
    ax.set_theta_direction(-1)          # Clockwise (Dawn to the right)
    ax.set_ylim(l_range)
    ax.set_title(title, pad=20)
    
    # MLT labels instead of degree labels
    mlt_labels = ['12', '15', '18', '21', '00', '03', '06', '09']
    ax.set_thetagrids(np.arange(0, 360, 45), labels=mlt_labels)
    ax.set_ylabel('L-shell', labelpad=30)
    
    # Initialise plot elements
    trail, = ax.plot([], [], 'o', markersize=2, alpha=0.3, color='grey')
    point, = ax.plot([], [], 'o', markersize=8, zorder=5)
    time_text = ax.text(0.02, 0.95, '', transform=ax.transAxes)
    
    # Add colourbar if colour data provided
    if color_data is not None:
        sm = plt.cm.ScalarMappable(cmap=cmap, 
                                    norm=plt.Normalize(c_min, c_max))
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=ax, pad=0.1, shrink=0.8)
        cbar.set_label(color_label)
    
    def init():
        trail.set_data([], [])
        point.set_data([], [])
        time_text.set_text('')
        return trail, point, time_text
    
    def update(frame):
        # Trail indices
        start = max(0, frame - trail_length)
        trail.set_data(theta[start:frame], r[start:frame])
        
        # Current position
        point.set_data([theta[frame]], [r[frame]])
        if color_data is not None:
            point.set_color(colormap(c_norm[frame]))
        
        # Time label
        time_text.set_text(f't = {time_hours[frame]:.1f} hrs')
        
        return trail, point, time_text
    
    # Subsample if dataset is very large
    step = max(1, len(time_hours) // 2000)
    frames = range(0, len(time_hours), step)
    
    anim = FuncAnimation(fig, update, frames=frames,
                         init_func=init, interval=interval, blit=True)
    
    if save_path:
        if save_path.endswith('.gif'):
            anim.save(save_path, writer='pillow', fps=30)
        else:
            anim.save(save_path, writer='ffmpeg', fps=30)
        print(f'Animation saved to {save_path}')
    
    return anim