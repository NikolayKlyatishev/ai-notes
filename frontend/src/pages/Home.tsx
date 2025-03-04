import LoginIcon from '@mui/icons-material/Login';
import MicIcon from '@mui/icons-material/Mic';
import NoteIcon from '@mui/icons-material/Note';
import SearchIcon from '@mui/icons-material/Search';
import {
    Box,
    Button,
    Card,
    CardContent,
    CircularProgress,
    Container,
    Grid,
    Paper,
    Stack,
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

                // Получаем последние заметки если пользователь авторизован
                if (isAuthenticated) {
                    try {
                        const notes = await apiService.notes.getAll();
                        setRecentNotes(notes.slice(0, 5)); // Берем только 5 последних заметок
                    } catch (err) {
                        console.error('Ошибка при загрузке заметок:', err);
                    }
                }

                // Получаем статус рекордера
                try {
                    const status = await apiService.recorder.getStatus();
                    setRecorderStatus(status);
                } catch (err) {
                    console.error('Ошибка при загрузке статуса рекордера:', err);
                }
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
                {/* Приветственная секция */}
                <Paper elevation={3} sx={{ p: 4, mb: 4, bgcolor: 'primary.light', color: 'white', borderRadius: 2 }}>
                    <Typography variant="h3" component="h1" gutterBottom sx={{ fontWeight: 'bold' }}>
                        Добро пожаловать в AI Notes
                    </Typography>

                    <Typography variant="h6" paragraph>
                        Система автоматической фиксации разговоров с использованием искусственного интеллекта
                    </Typography>

                    {!isAuthenticated && (
                        <Button
                            component={Link}
                            to="/login"
                            variant="contained"
                            color="secondary"
                            size="large"
                            startIcon={<LoginIcon />}
                            sx={{ mt: 2, fontWeight: 'bold', px: 3, py: 1.5 }}
                        >
                            Войти в систему
                        </Button>
                    )}

                    {isAuthenticated && user && (
                        <Typography variant="h5" sx={{ mt: 2 }}>
                            С возвращением, {user.username}!
                        </Typography>
                    )}
                </Paper>

                {error && (
                    <Typography color="error" sx={{ mb: 2 }}>
                        {error}
                    </Typography>
                )}

                {/* Основные функции */}
                <Typography variant="h5" gutterBottom sx={{ mb: 3, mt: 4 }}>
                    Основные возможности
                </Typography>

                <Grid container spacing={3} sx={{ mb: 4 }}>
                    <Grid item xs={12} md={4}>
                        <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column', transition: '0.3s', '&:hover': { transform: 'translateY(-5px)', boxShadow: 6 } }}>
                            <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
                                <NoteIcon color="primary" sx={{ fontSize: 60, mb: 2 }} />
                                <Typography variant="h6" gutterBottom>
                                    Управление заметками
                                </Typography>
                                <Typography variant="body2" paragraph sx={{ flexGrow: 1 }}>
                                    Создавайте, редактируйте и организуйте ваши заметки с помощью тегов и категорий
                                </Typography>
                                <Button
                                    component={Link}
                                    to="/notes"
                                    variant="outlined"
                                    color="primary"
                                    disabled={!isAuthenticated}
                                >
                                    Перейти к заметкам
                                </Button>
                            </CardContent>
                        </Card>
                    </Grid>

                    <Grid item xs={12} md={4}>
                        <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column', transition: '0.3s', '&:hover': { transform: 'translateY(-5px)', boxShadow: 6 } }}>
                            <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
                                <MicIcon color="error" sx={{ fontSize: 60, mb: 2 }} />
                                <Typography variant="h6" gutterBottom>
                                    Запись разговоров
                                </Typography>
                                <Typography variant="body2" paragraph sx={{ flexGrow: 1 }}>
                                    Записывайте аудио и автоматически преобразуйте его в текст с помощью технологии распознавания речи
                                </Typography>
                                <Button
                                    component={Link}
                                    to="/recorder"
                                    variant="outlined"
                                    color="error"
                                >
                                    Перейти к записи
                                </Button>
                            </CardContent>
                        </Card>
                    </Grid>

                    <Grid item xs={12} md={4}>
                        <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column', transition: '0.3s', '&:hover': { transform: 'translateY(-5px)', boxShadow: 6 } }}>
                            <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
                                <SearchIcon color="success" sx={{ fontSize: 60, mb: 2 }} />
                                <Typography variant="h6" gutterBottom>
                                    Умный поиск
                                </Typography>
                                <Typography variant="body2" paragraph sx={{ flexGrow: 1 }}>
                                    Быстро находите нужную информацию в своих заметках с помощью семантического поиска
                                </Typography>
                                <Button
                                    component={Link}
                                    to="/search"
                                    variant="outlined"
                                    color="success"
                                    disabled={!isAuthenticated}
                                >
                                    Перейти к поиску
                                </Button>
                            </CardContent>
                        </Card>
                    </Grid>
                </Grid>

                {/* Текущее состояние */}
                <Grid container spacing={3} sx={{ mt: 2 }}>
                    {/* Блок записи */}
                    <Grid item xs={12} md={6}>
                        <Card>
                            <CardContent>
                                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                                    <MicIcon sx={{ mr: 1 }} color={recorderStatus?.is_recording ? "error" : "disabled"} />
                                    Статус записи
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
                                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                                    <NoteIcon sx={{ mr: 1 }} />
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
                                    <Stack spacing={2}>
                                        <Typography variant="body2" color="text.secondary">
                                            Войдите, чтобы увидеть ваши заметки
                                        </Typography>
                                        <Button
                                            component={Link}
                                            to="/login"
                                            variant="outlined"
                                        >
                                            Войти
                                        </Button>
                                    </Stack>
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