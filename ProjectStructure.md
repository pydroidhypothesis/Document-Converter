main/
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── base_converter.py
│   │   ├── file_utils.py
│   │   └── exceptions.py
│   ├── converters/
│   │   ├── __init__.py
│   │   ├── document_converters.py
│   │   ├── image_converters.py
│   │   ├── audio_converters.py
│   │   ├── video_converters.py
│   │   ├── archive_converters.py
│   │   ├── data_converters.py
│   │   ├── ebook_converters.py
│   │   └── cad_converters.py
│   ├── compressors/
│   │   ├── __init__.py
│   │   ├── zip_compressor.py
│   │   ├── tar_compressor.py
│   │   ├── gz_compressor.py
│   │   ├── bz2_compressor.py
│   │   ├── xz_compressor.py
│   │   └── seven_z_compressor.py
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── batch_processor.py
│   │   ├── watch_service.py
│   │   └── pipeline.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── validators.py
│   │   ├── formatters.py
│   │   └── logger.py
│   └── web/
│       ├── __init__.py
│       ├── static/
│       │   ├── css/
│       │   │   └── style.css
│       │   └── js/
│       │       ├── main.js
│       │       └── converters.js
│       └── templates/
│           └── index.html
├── tests/
│   ├── __init__.py
│   ├── test_converters.py
│   ├── test_compressors.py
│   └── test_utils.py
├── docs/
│   ├── api.md
│   └── user_guide.md
├── config/
│   ├── default_config.yaml
│   └── logging_config.yaml
├── scripts/
│   ├── install_deps.sh
│   └── run_tests.sh
├── batch_processor.py
├── document_converter.py
├── gui_launcher.py
├── index.html
├── style.css
├── README.md
├── requirements.txt
├── setup.py
└── .env.example
