const { BASE_URL } = require('./src/api');
const fs = require("fs");
const path = require("path");
const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true
})

module.exports = {
  devServer: {
    https: {
      key: fs.readFileSync(path.resolve(__dirname, '../backend/server.key')),
      cert: fs.readFileSync(path.resolve(__dirname, '../backend/server.crt')),
    },
    // 注意：必须使用证书中对应的域名来启动前端服务
    host: "0.0.0.0",
    port: 8080,
    open: true,
    proxy: {
      '/api': {
        target: BASE_URL,
        changeOrigin: true,
        secure: false  // 绕过后端自签名证书的校验
      }
    }
  },
};
