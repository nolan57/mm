#!/bin/bash

# Create static directories if they don't exist
mkdir -p static/vendor/{jquery,jquery-ui,formbuilder}
mkdir -p static/js/tinymce/tinymce/js/tinymce/langs

# Download jQuery
curl -L https://code.jquery.com/jquery-3.6.0.min.js -o static/vendor/jquery/jquery.min.js

# Download jQuery UI
curl -L https://code.jquery.com/ui/1.13.2/jquery-ui.min.js -o static/vendor/jquery-ui/jquery-ui.min.js

# Download Form Builder
curl -L https://formbuilder.online/assets/js/form-builder.min.js -o static/vendor/formbuilder/form-builder.min.js

# Download TinyMCE
curl -L https://cdn.tiny.cloud/1/no-api-key/tinymce/6/tinymce.min.js -o static/js/tinymce/tinymce/js/tinymce/tinymce.min.js
curl -L https://cdn.tiny.cloud/1/no-api-key/tinymce/6/langs/zh_CN.js -o static/js/tinymce/tinymce/js/tinymce/langs/zh_CN.js
