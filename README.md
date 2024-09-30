# guy-nodes-comfyui

These are designed to be custom nodes i found usefulness to that hopefully others can share. 

__Empty Latent creation by desired size with scale__

This node is for knowing the desired output images sizes and reverse engineering based on what SDXL supports. It will them output a blank Latent, the Width/Height of it, the CLIP Widy/Height based on a scale, and lastly a ratio for your Upscaler. 

This is all based on this repo: https://github.com/marhensa/sdxl-recommended-res-calc who created a great tool and I just enhanced it for my needs. 
