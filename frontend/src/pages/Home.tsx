import {
    Box,
    Button,
    Card,
    CardContent,
    CircularProgress,
    Container,
    Grid,
    Typography
} from '@mui/material';
import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { apiService, Note, RecorderStatus } from '../services/api';

const Home: React.FC = () => {
    const { isAuthenticated, user } = useAuth();
    const [recentNotes, setRecentNotes] = useState<Note[]>([]);
    const [recorderStatus, setRecorderStatus] = useState<RecorderStatus | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setIsLoading(true);
                setError(null);

                // Получаем последние заметки
                if (isAuthenticated) {
                    const notes = await apiService.notes.getAll();
                    setRecentNotes(notes.slice(0, 5)); // Берем только 5 последних заметок
                }

                // Получаем статус рекордера
                const status = await apiService.recorder.getStatus();
                setRecorderStatus(status);
            } catch (err) {
                console.error('Ошибка при загрузке данных:', err);
                setError('Не удалось загрузить данные. Пожалуйста, попробуйте позже.');
            } finally {
                setIsLoading(false);
            }
        };

        fetchData();
    }, [isAuthenticated]);

    const handleStartRecording = async () => {
        try {
            await apiService.recorder.start();
            // Обновляем статус рекордера
            const status = await apiService.recorder.getStatus();
            setRecorderStatus(status);
        } catch (err) {
            console.error('Ошибка при запуске записи:', err);
            setError('Не удалось запустить запись. Пожалуйста, попробуйте позже.');
        }
    };

    const handleStopRecording = async () => {
        try {
            await apiService.recorder.stop();
            // Обновляем статус рекордера
            const status = await apiService.recorder.getStatus();
            setRecorderStatus(status);
        } catch (err) {
            console.error('Ошибка при остановке записи:', err);
            setError('Не удалось остановить запись. Пожалуйста, попробуйте позже.');
        }
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
                    Добро пожаловать в AI Notes
                    {isAuthenticated && user && `, ${user.username}!`}
                </Typography>

                <Typography variant="body1" paragraph>
                    AI Notes - система автоматической фиксации разговоров и создания заметок с использованием искусственного интеллекта.
                </Typography>

                {error && (
                    <Typography color="error" sx={{ mb: 2 }}>
                        {error}
                    </Typography>
                )}

                <Grid container spacing={3} sx={{ mt: 2 }}>
                    {/* Блок записи */}
                    <Grid item xs={12} md={6}>
                        <Card>
                            <CardContent>
                                <Typography variant="h6" gutterBottom>
                                    Запись разговора
                                </Typography>

                                <Typography variant="body2" color="text.secondary" paragraph>
                                    {recorderStatus?.is_recording
                                        ? `Запись активна: ${Math.floor(recorderStatus.duration)} сек.`
                                        : 'Запись не активна'}
                                </Typography>

                                <Box sx={{ mt: 2 }}>
                                    {recorderStatus?.is_recording ? (
                                        <Button
                                            variant="contained"
                                            color="error"
                                            onClick={handleStopRecording}
                                        >
                                            Остановить запись
                                        </Button>
                                    ) : (
                                        <Button
                                            variant="contained"
                                            color="primary"
                                            onClick={handleStartRecording}
                                        >
                                            Начать запись
                                        </Button>
                                    )}
                                </Box>
                            </CardContent>
                        </Card>
                    </Grid>

                    {/* Блок последних заметок */}
                    <Grid item xs={12} md={6}>
                        <Card>
                            <CardContent>
                                <Typography variant="h6" gutterBottom>
                                    Последние заметки
                                </Typography>

                                {isAuthenticated ? (
                                    <>
                                        {recentNotes.length > 0 ? (
                                            <Box>
                                                {recentNotes.map((note) => (
                                                    <Box key={note.id} sx={{ mb: 1 }}>
                                                        <Link to={`/notes/${note.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                                                            <Typography variant="body2">
                                                                {note.title}
                                                            </Typography>
                                                        </Link>
                                                    </Box>
                                                ))}
                                            </Box>
                                        ) : (
                                            <Typography variant="body2" color="text.secondary">
                                                У вас пока нет заметок
                                            </Typography>
                                        )}

                                        <Button
                                            component={Link}
                                            to="/notes"
                                            variant="outlined"
                                            sx={{ mt: 2 }}
                                        >
                                            Все заметки
                                        </Button>
                                    </>
                                ) : (
                                    <Typography variant="body2" color="text.secondary">
                                        Войдите, чтобы увидеть ваши заметки
                                    </Typography>
                                )}
                            </CardContent>
                        </Card>
                    </Grid>
                </Grid>
            </Box>
        </Container>
    );
};

export default Home; 