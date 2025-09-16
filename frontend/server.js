const express = require('express');
const app = express();
const path = require('path');

// 设置静态文件目录
app.use(express.static(__dirname));

const port = 8080;
app.listen(port, () => {
    console.log(`Server is running on port ${port}`);
}); 