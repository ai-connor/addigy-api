# TODO - Ensure openapi tools are installed:
# npm install @openapitools/openapi-generator-cli -g
openapi-generator-cli generate \
    -i ../../_addigy_api.json \
    -g go \
    -o ../../ \
    -c config.yaml \
    --skip-validate-spec \
    --git-user-id ai-connor \
    --git-repo-id addigy-api

# Post-generation fixups (e.g. free-form values -> interface{}); see postprocess.py.
python3 postprocess.py

cd ../..
go fmt