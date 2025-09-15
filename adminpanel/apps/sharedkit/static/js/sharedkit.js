function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        // 使用现代Clipboard API
        navigator.clipboard.writeText(text).then(function() {
            layer.alert('路径已复制到剪贴板',{icon: 1,title: null});
        }, function(err) {
            console.error('复制失败:', err);
            layer.alert('路径复制失败', {icon: 2,title: null});
        });
    } else {
        fallbackCopyTextToClipboard(text);
    }
}

function fallbackCopyTextToClipboard(text) {
    var textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.position = "fixed";
    textArea.style.left = "-999999px";
    textArea.style.top = "-999999px";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    try {
        var successful = document.execCommand('copy');
        if (successful) {
            layer.msg('路径已复制到剪贴板');
        } else {
            layer.alert('路径复制失败', {icon: 2,title: null});
        }
    } catch (err) {
        layer.alert('路径复制失败', {icon: 2,title: null});
        console.error('复制失败:', err);
    }
    document.body.removeChild(textArea);
}


function openTerminal(path) {
    path = path.replace('/', '\\')
    layer.msg('尝试打开终端!请检查屏幕或者任务栏~');
    fetch(path, {
        method: 'GET'
    })
    .then(response => response.json())
    .then(data => {
        console.log('尝试打开终端:', data);
        if (data.status === 'success') {
        } else {
             layer.alert('终端打开失败~' + data.message, {
                 icon: 2, title: null,
             });
        }
    })
    .catch(error => {
        layer.alert('终端打开失败，未知错误！' + data.message, {icon: 2, title: null});
        console.error('Error:', error);
    });
}

function openFolder(path) {
    layer.msg('尝试打开资源管理器!请检查屏幕或者任务栏~');
    fetch(path, {
        method: 'GET'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
        } else {
            layer.alert('资源管理器打开失败: ' + data.message, {icon: 2, title: null});
        }
    })
}

function OpenSystemEnvironmentVariables(url){
    layer.msg('尝试打开系统环境变量属性!请检查屏幕或者任务栏~');
    fetch(url, {
        method: 'GET'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
        } else {
            layer.alert('系统环境变量属性打开失败: ' + data.message, {icon: 2, title: null});
        }
    })
}
