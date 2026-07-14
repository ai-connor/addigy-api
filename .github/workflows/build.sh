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

cd ../..
go fmt