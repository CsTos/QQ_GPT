import replicate


def get_stable_diffusion_img(json,api_token):
    model = replicate.Client(api_token=api_token).models.get(
        "cjwbw/dreamshaper")
    version = model.versions.get("ed6d8bee9a278b0d7125872bddfb9dd3fc4c401426ad634d8246a660e387475b")
    inputs = {
        # 提示词
        'prompt': json['prompt'],
        # 分辨率
        'width': json['width'],
        'height': json['height'],
        # 反向提示词
        'negative_prompt': json['negative_prompt'],
        # 输出图片数量
        # Range: 1 to 4
        'num_outputs': 1,
        # Number of denoising steps
        # Range: 1 to 500
        'num_inference_steps': json['num_inference_steps'],

        # Scale for classifier-free guidance
        # Range: 1 to 20
        'guidance_scale': json['guidance_scale'],

        # Choose a scheduler.
        'scheduler': json['scheduler'],

        # Random seed. Leave blank to randomize the seed
        'seed': json['seed'],
    }
    output = version.predict(**inputs)
    return output


if __name__ == '__main__':
    print(get_stable_diffusion_img({
        "prompt": "(golden orange gradient hair)),(red eyes),(game_cg),(double_bun),(low twintails),solo,((flat_chest)),((glasses)),(symbol in eye),masterpiece,best quality,highly detailed,1girl,(artbook),(incredibly_absurdres),huge_filesize,((yellow necktie)),(trench coat),((pleated_skirt)),small breasts,Exquisite background,sit on the sofa,laugh,((library)",
        "width": 768,
        "height": 512,
        "negative_prompt": "",
        "num_inference_steps": 20,
        "guidance_scale": 7.5,
        "scheduler": "K_EULER_ANCESTRAL",
        "seed": 1
    }, ""))
