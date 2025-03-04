import {
    Mic as MicIcon,
    Refresh as RefreshIcon,
    Stop as StopIcon
} from '@mui/icons-material';
import {
    Alert,
    Box,
    Button,
    Card,
    CardContent,
    CircularProgress,
    Container,
    Divider,
    Grid,
    LinearProgress,
    Paper,
    Typography
} from '@mui/material';
import React, { useEffect, useState } from 'react';
import { apiService, RecorderStatus } from '../services/api';

const Recorder: React.FC = () => {
    const [recorderStatus, setRecorderStatus] = useState<RecorderStatus | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isStarting, setIsStarting] = useState(false);
    const [isStopping, setIsStopping] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [elapsedTime, setElapsedTime] = useState(0);

    // Получение статуса рекордера
    const fetchRecorderStatus = async () => {
        try {
            setError(null);
            const status = await apiService.recorder.getStatus();
            setRecorderStatus(status);
            setElapsedTime(status.duration);
        } catch (err) {
            console.error('Ошибка при получении статуса рекордера:', err);
            setError('Не удалось получить статус рекордера. Пожалуйста, попробуйте позже.');
        } finally {
            setIsLoading(false);
        }
    };

    // Запуск рекордера
    const handleStartRecording = async () => {
        try {
            setIsStarting(true);
            setError(null);
            await apiService.recorder.start();
            await fetchRecorderStatus();
        } catch (err) {
            console.error('Ошибка при запуске записи:', err);
            setError('Не удалось запустить запись. Пожалуйста, попробуйте позже.');
        } finally {
            setIsStarting(false);
        }
    };

    // Остановка рекордера
    const handleStopRecording = async () => {
        try {
            setIsStopping(true);
            setError(null);
            await apiService.recorder.stop();
            await fetchRecorderStatus();
        } catch (err) {
            console.error('Ошибка при остановке записи:', err);
            setError('Не удалось остановить запись. Пожалуйста, попробуйте позже.');
        } finally {
            setIsStopping(false);
        }
    };

    // Обновление таймера
    useEffect(() => {
        let timer: number | undefined = undefined;

        if (recorderStatus?.is_recording) {
            timer = setInterval(() => {
                setElapsedTime(prev => prev + 1);
            }, 1000);
        }

        return () => {
            if (timer) {
                clearInterval(timer);
            }
        };
    }, [recorderStatus?.is_recording]);

    // Загрузка статуса при монтировании
    useEffect(() => {
        fetchRecorderStatus();
    }, []);

    // Форматирование времени
    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    if (isLoading) {
        return (
            <Container maxWidth="md">
                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}>
                    <CircularProgress />
                </Box>
            </Container>
        );
    }

    return (
        <Container maxWidth="md">
            <Box sx={{ my: 4 }}>
                <Typography variant="h4" component="h1" gutterBottom>
                    Запись разговора
                </Typography>

                <Typography variant="body1" paragraph>
                    Используйте этот инструмент для записи разговоров и автоматического создания заметок на их основе.
                </Typography>

                {error && (
                    <Alert severity="error" sx={{ mb: 3 }}>
                        {error}
                    </Alert>
                )}

                <Grid container spacing={3}>
                    <Grid item xs={12}>
                        <Card>
                            <CardContent>
                                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 3 }}>
                                    <Paper
                                        elevation={3}
                                        sx={{
                                            width: 120,
                                            height: 120,
                                            borderRadius: '50%',
                                            display: 'flex',
                                            justifyContent: 'center',
                                            alignItems: 'center',
                                            mb: 3,
                                            bgcolor: recorderStatus?.is_recording ? 'error.main' : 'primary.main'
                                        }}
                                    >
                                        {recorderStatus?.is_recording ? (
                                            <StopIcon sx={{ fontSize: 60, color: 'white' }} />
                                        ) : (
                                            <MicIcon sx={{ fontSize: 60, color: 'white' }} />
                                        )}
                                    </Paper>

                                    <Typography variant="h5" gutterBottom>
                                        {recorderStatus?.is_recording ? 'Запись активна' : 'Запись не активна'}
                                    </Typography>

                                    {recorderStatus?.is_recording && (
                                        <Box sx={{ width: '100%', mb: 2 }}>
                                            <Typography variant="h3" align="center" sx={{ mb: 1 }}>
                                                {formatTime(elapsedTime)}
                                            </Typography>
                                            <LinearProgress color="error" />
                                        </Box>
                                    )}

                                    <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
                                        {recorderStatus?.is_recording ? (
                                            <Button
                                                variant="contained"
                                                color="error"
                                                size="large"
                                                startIcon={<StopIcon />}
                                                onClick={handleStopRecording}
                                                disabled={isStopping}
                                            >
                                                {isStopping ? 'Остановка...' : 'Остановить запись'}
                                            </Button>
                                        ) : (
                                            <Button
                                                variant="contained"
                                                color="primary"
                                                size="large"
                                                startIcon={<MicIcon />}
                                                onClick={handleStartRecording}
                                                disabled={isStarting}
                                            >
                                                {isStarting ? 'Запуск...' : 'Начать запись'}
                                            </Button>
                                        )}

                                        <Button
                                            variant="outlined"
                                            startIcon={<RefreshIcon />}
                                            onClick={fetchRecorderStatus}
                                        >
                                            Обновить статус
                                        </Button>
                                    </Box>
                                </Box>

                                <Divider sx={{ my: 3 }} />

                                <Typography variant="h6" gutterBottom>
                                    Инструкция по использованию
                                </Typography>

                                <Typography variant="body2" paragraph>
                                    1. Нажмите "Начать запись", чтобы начать запись разговора.
                                </Typography>
                                <Typography variant="body2" paragraph>
                                    2. Говорите четко и ясно для лучшего распознавания речи.
                                </Typography>
                                <Typography variant="body2" paragraph>
                                    3. Нажмите "Остановить запись", когда разговор закончен.
                                </Typography>
                                <Typography variant="body2" paragraph>
                                    4. Система автоматически создаст заметку на основе записанного разговора.
                                </Typography>
                                <Typography variant="body2" paragraph>
                                    5. Вы можете найти созданную заметку в разделе "Заметки".
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                </Grid>
            </Box>
        </Container>
    );
};

export default Recorder; 