"""

This is the ComfyUI custom node, 
    
A custom node for ComfyUI to automatically set the recommended initial latent size and clip sizes
for SDXL image generation and its Upscale Factor 
based on the desired Final Resolution output 

Marhensa Aditya Hadi (2023)
    
"""

# As Per CapsAdmin (https://github.com/CapsAdmin) suggest, it could be a ComfyUI Custom Node if modified.
# https://github.com/marhensa/sdxl-recommended-res-calc/issues/1
# This is his/her edit add suggestion
# Many thanks!

# Accepted aspect ratios and corresponding XSIZE, YSIZE, and NUMRATIO
# Accepted aspect ratios and pixel size is derived from this SDXL paper
# https://arxiv.org/abs/2307.01952 https://arxiv.org/pdf/2307.01952.pdf
# Page 17 "We use the following image resolutions for mixed-aspect ratio finetuning as described in Section 2.3"

from nodes import EmptyLatentImage

# Horizontal aspect ratio
accepted_ratios_horizontal = {
    "4:1": (2048, 512, 4.000000000),
    "31:8": (1984, 512, 3.875000000),
    "15:4": (1920, 512, 3.750000000),
    "29:8": (1856, 512, 3.625000000),
    "28:9": (1792, 576, 3.111111111),
    "3:1": (1728, 576, 3.000000000),
    "26:9": (1664, 576, 2.888888889),
    "5:2": (1600, 640, 2.500000000),
    "12:5": (1536, 640, 2.400000000),
    "23:11": (1472, 704, 2.090909091),
    "2:1": (1408, 704, 2.000000000),
    "21:11": (1344, 704, 1.909090909),
    "7:4": (1344, 768, 1.750000000),
    "5:3": (1280, 768, 1.666666667),
    "19:13": (1216, 832, 1.461538462),
    "18:13": (1152, 832, 1.384615385),
    "9:7": (1152, 896, 1.285714286),
    "17:14": (1088, 896, 1.214285714),
    "17:15": (1088, 960, 1.133333333),
    "16:15": (1024, 960, 1.066666667)
}

# Vertical aspect ratio
accepted_ratios_vertical = {
    "15:16": (960, 1024, 0.937500000),
    "15:17": (960, 1088, 0.882352941),
    "14:17": (896, 1088, 0.823529412),
    "7:9": (896, 1152, 0.777777778),
    "13:18": (832, 1152, 0.722222222),
    "13:19": (832, 1216, 0.684210526),
    "3:5": (768, 1280, 0.600000000),
    "4:7": (768, 1344, 0.571428571),
    "11:21": (704, 1344, 0.523809524),
    "1:2": (704, 1408, 0.500000000),
    "11:23": (704, 1472, 0.478260870),
    "5:12": (640, 1536, 0.416666667),
    "2:5": (640, 1600, 0.400000000),
    "9:26": (576, 1664, 0.346153846),
    "1:3": (576, 1728, 0.333333333),
    "9:28": (576, 1792, 0.321428571),
    "8:29": (512, 1856, 0.275862069),
    "4:15": (512, 1920, 0.266666667),
    "8:31": (512, 1984, 0.258064516),
    "1:4": (512, 2048, 0.250000000)
}

# Square aspect ratio
accepted_ratios_square = {
    "1:1": (1024, 1024, 1.00000000)
}


class GuyRecommendedLatentResCalc:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "desiredWidth": ("INT", {
                    "default": 1024,
                    "min": 0,  # Minimum value
                    "max": 8192,  # Maximum value
                    "step": 2  # Slider's step
                }),
                "desiredHeight": ("INT", {
                    "default": 1024,
                    "min": 0,  # Minimum value
                    "max": 8192,  # Maximum value
                    "step": 2  # Slider's step
                }),
                "clip_scale": ("FLOAT", {
                    "default": 2.0,
                    "min": 1.0,
                    "max": 10.0,
                    "step": .5
                }),
                "batch_size": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 64
                }),
            },
        }

    RETURN_TYPES = ("LATENT", "INT", "INT", "INT", "INT", "FLOAT")
    RETURN_NAMES = (
        "LATENT",
        "LATENT_WIDTH",
        "LATENT_HEIGHT",
        "CLIP_WIDTH",
        "CLIP_HEIGHT",
        "RESCALE_FACTOR"
    )
    FUNCTION = "calc"
    CATEGORY = "utils"

    def calc(self, desiredWidth, desiredHeight, clip_scale, batch_size):
        # Calculate the aspect ratio of the desired size
        desired_ratio = desiredWidth / desiredHeight

        # Find the closest accepted aspect ratio
        closest_ratio = None
        closest_diff = float('inf')

        for ratio, (x_size, y_size, num_ratio) in accepted_ratios_horizontal.items():
            diff = abs(num_ratio - desired_ratio)
            if diff < closest_diff:
                closest_ratio = ratio
                closest_diff = diff

        for ratio, (x_size, y_size, num_ratio) in accepted_ratios_vertical.items():
            diff = abs(num_ratio - desired_ratio)
            if diff < closest_diff:
                closest_ratio = ratio
                closest_diff = diff

        # Compare with square aspect ratio
        x_size, y_size, num_ratio = accepted_ratios_square["1:1"]
        diff = abs(num_ratio - desired_ratio)
        if diff < closest_diff:
            closest_ratio = "1:1"

        if closest_ratio in accepted_ratios_horizontal:
            accepted_XSIZE, accepted_YSIZE, _ = accepted_ratios_horizontal[closest_ratio]
        elif closest_ratio in accepted_ratios_vertical:
            accepted_XSIZE, accepted_YSIZE, _ = accepted_ratios_vertical[closest_ratio]
        else:
            accepted_XSIZE, accepted_YSIZE, _ = accepted_ratios_square[closest_ratio]

        upscale_factor_width = desiredWidth / accepted_XSIZE
        upscale_factor_height = desiredHeight / accepted_YSIZE

        # Compare the upscale factors for width and height and select the larger one
        if upscale_factor_width >= upscale_factor_height:
            scaling_factor = round(upscale_factor_width, 9)
        else:
            scaling_factor = round(upscale_factor_height, 9)

        latent = EmptyLatentImage().generate(
            accepted_XSIZE, accepted_YSIZE, batch_size)[0]

        return (
            latent,
            accepted_XSIZE,
            accepted_YSIZE,
            int(accepted_XSIZE * clip_scale),
            int(accepted_YSIZE * clip_scale),
            scaling_factor
        )


# A dictionary that contains all nodes you want to export with their names
# NOTE: names should be globally unique
NODE_CLASS_MAPPINGS = {
    "GuyRecommendedLatentResCalc": GuyRecommendedLatentResCalc
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "GuyRecommendedLatentResCalc": "Guy Recommended Resolution Calculator and Latent Generator"
}
