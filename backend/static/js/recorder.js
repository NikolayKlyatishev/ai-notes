// Обновление статуса рекордера
function updateStatus() {
    $.ajax({
        url: '/api/recorder/status',
        method: 'GET',
        success: function(data) {
            console.log("Статус рекордера:", data);
            
            // Обновляем UI в зависимости от состояния
            if (data.running) {
                $('#recordButton').addClass('btn-danger').removeClass('btn-primary').text('Остановить запись');
                $('#recordButton').data('action', 'stop');
                
                // Обновляем продолжительность
                if (data.duration) {
                    const minutes = Math.floor(data.duration / 60);
                    const seconds = data.duration % 60;
                    $('#recordingTime').text(`${minutes}:${seconds < 10 ? '0' : ''}${seconds}`);
                    $('#recordingInfo').show();
                }
                
                // Обновляем уровень звука
                if (data.audio_level) {
                    updateAudioMeter(data.audio_level);
                }
                
                // Показываем текущий файл записи
                if (data.current_file) {
                    $('#currentFile').text(data.current_file);
                    $('#currentFileInfo').show();
                }
            } else {
                $('#recordButton').addClass('btn-primary').removeClass('btn-danger').text('Начать запись');
                $('#recordButton').data('action', 'start');
                $('#recordingInfo').hide();
                $('#currentFileInfo').hide();
                resetAudioMeter();
                
                // Проверяем статус транскрибирования
                if (data.transcribing) {
                    // Показываем информацию о прогрессе транскрибирования
                    const progress = data.transcribe_progress;
                    const percent = progress.total_files > 0 
                        ? Math.round((progress.processed_files / progress.total_files) * 100) 
                        : 0;
                    
                    $('#transcribeStatus').html(`
                        <div class="alert alert-info">
                            <i class="fas fa-sync fa-spin"></i> Транскрибирование: ${progress.processed_files}/${progress.total_files} файлов (${percent}%)
                            ${progress.current_file ? `<br>Текущий файл: ${progress.current_file}` : ''}
                        </div>
                    `);
                    $('#transcribeStatus').show();
                } else {
                    $('#transcribeStatus').hide();
                }
            }
            
            // Обновляем список последних записей
            if (data.recent_files && Array.isArray(data.recent_files)) {
                updateRecentRecordings(data.recent_files);
            }
        },
        error: function(xhr, status, error) {
            console.error("Ошибка при получении статуса:", error);
        },
        complete: function() {
            // Продолжаем обновление, если страница активна
            if (pageActive) {
                setTimeout(updateStatus, 1000);
            }
        }
    });
} 