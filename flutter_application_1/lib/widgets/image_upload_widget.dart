import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_dropzone/flutter_dropzone.dart';
//import 'package:image_picker/image_picker.dart';

class ImageUploadWidget extends StatefulWidget {
  final File? selectedImage;
  final Uint8List? selectedImageBytes;  // 添加字节数据
  final Function(File, Uint8List?) onImageSelected;  // 修改回调函数
  final VoidCallback onPickImage;

  const ImageUploadWidget({
    super.key,
    required this.selectedImage,
    required this.selectedImageBytes,
    required this.onImageSelected,
    required this.onPickImage,
  });

  @override
  State<ImageUploadWidget> createState() => _ImageUploadWidgetState();
}

class _ImageUploadWidgetState extends State<ImageUploadWidget> {
  late DropzoneViewController controller;
  bool isDragging = false;
  Uint8List? _imageBytes;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 400,//修改高度
      decoration: BoxDecoration(
        border: Border.all(
          color: isDragging ? Colors.blue : Colors.grey,
          width: 2,
          style: BorderStyle.solid,
        ),
        borderRadius: BorderRadius.circular(12),
        color: isDragging ? Colors.blue.withOpacity(0.1) : Colors.grey.withOpacity(0.05),
      ),
      child: Stack(
        children: [
          // 拖拽区域
          DropzoneView(
            operation: DragOperation.copy,
            cursor: CursorType.grab,
            onCreated: (ctrl) => controller = ctrl,
            onLoaded: () => print('Zone loaded'),
            onError: (ev) => print('Zone error: $ev'),
            onHover: () {
              setState(() {
                isDragging = true;
              });
            },
            onLeave: () {
              setState(() {
                isDragging = false;
              });
            },
            onDrop: (ev) async {
              setState(() {
                isDragging = false;
              });
              
              final name = await controller.getFilename(ev);
              final mime = await controller.getFileMIME(ev);
              final bytes = await controller.getFileData(ev);
              
              // 检查文件类型
              if (!mime.startsWith('image/')) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('请上传图片文件')),
                );
                return;
              }
              
              // 保存字节数据
              setState(() {
                _imageBytes = bytes;
              });
              
              // 创建临时文件对象（仅用于API调用）
              final tempFile = await _saveBytesToTempFile(bytes, name);
              if (tempFile != null) {
                widget.onImageSelected(tempFile, bytes);
              }
            },
          ),
          
          // 内容覆盖层
          Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                if (widget.selectedImageBytes != null || _imageBytes != null) ...[
                  // 显示选中的图片（使用字节数据）
                  Container(
                    width: 400,
                    height: 300,
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.grey),
                    ),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: Image.memory(
                        widget.selectedImageBytes ?? _imageBytes!,
                        fit: BoxFit.cover,
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    widget.selectedImage?.path.split('/').last ?? '上传的图片',
                    style: const TextStyle(fontSize: 14, color: Colors.grey),
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton.icon(
                    onPressed: () {
                      setState(() {
                        _imageBytes = null;
                      });
                      widget.onImageSelected(File(''), null);
                    },
                    icon: const Icon(Icons.refresh),
                    label: const Text('重新选择'),
                  ),
                ] else ...[
                  // 显示上传提示
                  Icon(
                    isDragging ? Icons.cloud_upload : Icons.cloud_upload_outlined,
                    size: 64,
                    color: isDragging ? Colors.blue : Colors.grey,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    isDragging ? '释放文件以上传' : '拖拽图片到这里或点击选择',
                    style: TextStyle(
                      fontSize: 16,
                      color: isDragging ? Colors.blue : Colors.grey[600],
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    '支持 PNG, JPG, JPEG 格式',
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.grey[500],
                    ),
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton.icon(
                    onPressed: widget.onPickImage,
                    icon: const Icon(Icons.folder_open),
                    label: const Text('选择文件'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.blue,
                      foregroundColor: Colors.white,
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }

  Future<File?> _saveBytesToTempFile(Uint8List bytes, String filename) async {
    try {
      // 在Web环境中，我们创建一个临时的File对象
      // 实际的文件操作会在API服务中处理
      final tempDir = Directory.systemTemp;
      final file = File('${tempDir.path}/$filename');
      await file.writeAsBytes(bytes);
      return file;
    } catch (e) {
      print('保存文件失败: $e');
      return null;
    }
  }
}