const fs = require("fs");
const path = require("path");

module.exports = {
  devServer: {
    https: {
      key: fs.readFileSync(path.resolve(__dirname, '../backend/server.key')),
      cert: fs.readFileSync(path.resolve(__dirname, '../backend/server.crt')),
    },
    // 注意：必须使用证书中对应的域名来启动前端服务
    host: "10.135.38.13",
    port: 8080,
    open: true,
    proxy: {
      '/api': {
        target: 'https://10.135.38.13:443',
        changeOrigin: true,
        secure: false  // 绕过后端自签名证书的校验
      }
    }
  },
};
