import replicate
from config_file import config_data


def img_to_prompt(img_url):
    model = replicate.Client(api_token=config_data['replicate']['api_token']).models.get("methexis-inc/img2prompt")
    version = model.versions.get("50adaf2d3ad20a6f911a8a9e3ccf777b263b8596fbd2c8fc26e8888f8a0edbb5")
    inputs = {
        'image': img_url,
    }
    output = version.predict(**inputs)
    return output


if __name__ == '__main__':
    img_to_prompt("https://c2cpicdw.qpic.cn/offpic_new/975023381//975023381-2152449928-81E5F77E675E6834E6D59DBBB3DDC43F/0?term=2&amp;is_origin=0")
