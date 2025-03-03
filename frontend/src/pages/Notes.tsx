import { Add as AddIcon, Delete as DeleteIcon, Edit as EditIcon } from '@mui/icons-material';
import {
    Alert,
    Box,
    Button,
    Card,
    CardActions,
    CardContent,
    Chip,
    CircularProgress,
    Container,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    Grid,
    IconButton,
    Snackbar,
    TextField,
    Typography
} from '@mui/material';
import React, { useEffect, useState } from 'react';
import { apiService, Note } from '../services/api';

const Notes: React.FC = () => {
    const [notes, setNotes] = useState<Note[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [openDialog, setOpenDialog] = useState(false);
    const [editingNote, setEditingNote] = useState<Note | null>(null);
    const [formData, setFormData] = useState({ title: '', content: '', tags: '' });
    const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });

    // Загрузка заметок
    const fetchNotes = async () => {
        try {
            setIsLoading(true);
            setError(null);
            const data = await apiService.notes.getAll();
            setNotes(data);
        } catch (err) {
            console.error('Ошибка при загрузке заметок:', err);
            setError('Не удалось загрузить заметки. Пожалуйста, попробуйте позже.');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchNotes();
    }, []);

    // Обработчики формы
    const handleOpenDialog = (note?: Note) => {
        if (note) {
            setEditingNote(note);
            setFormData({
                title: note.title,
                content: note.content,
                tags: note.tags.join(', ')
            });
        } else {
            setEditingNote(null);
            setFormData({ title: '', content: '', tags: '' });
        }
        setOpenDialog(true);
    };

    const handleCloseDialog = () => {
        setOpenDialog(false);
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    // Сохранение заметки
    const handleSaveNote = async () => {
        try {
            const { title, content, tags } = formData;
            const tagsArray = tags.split(',').map(tag => tag.trim()).filter(tag => tag);

            if (editingNote) {
                // Обновление существующей заметки
                await apiService.notes.update(editingNote.id, {
                    title,
                    content,
                    tags: tagsArray
                });
                setSnackbar({ open: true, message: 'Заметка обновлена', severity: 'success' });
            } else {
                // Создание новой заметки
                await apiService.notes.create({
                    title,
                    content,
                    tags: tagsArray
                });
                setSnackbar({ open: true, message: 'Заметка создана', severity: 'success' });
            }

            handleCloseDialog();
            fetchNotes(); // Обновляем список заметок
        } catch (err) {
            console.error('Ошибка при сохранении заметки:', err);
            setSnackbar({
                open: true,
                message: 'Не удалось сохранить заметку. Пожалуйста, попробуйте позже.',
                severity: 'error'
            });
        }
    };

    // Удаление заметки
    const handleDeleteNote = async (id: string) => {
        try {
            await apiService.notes.delete(id);
            setNotes(notes.filter(note => note.id !== id));
            setSnackbar({ open: true, message: 'Заметка удалена', severity: 'success' });
        } catch (err) {
            console.error('Ошибка при удалении заметки:', err);
            setSnackbar({
                open: true,
                message: 'Не удалось удалить заметку. Пожалуйста, попробуйте позже.',
                severity: 'error'
            });
        }
    };

    const handleCloseSnackbar = () => {
        setSnackbar(prev => ({ ...prev, open: false }));
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
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                    <Typography variant="h4" component="h1">
                        Заметки
                    </Typography>
                    <Button
                        variant="contained"
                        startIcon={<AddIcon />}
                        onClick={() => handleOpenDialog()}
                    >
                        Новая заметка
                    </Button>
                </Box>

                {error && (
                    <Typography color="error" sx={{ mb: 2 }}>
                        {error}
                    </Typography>
                )}

                {notes.length === 0 ? (
                    <Typography variant="body1" color="text.secondary" sx={{ mt: 4, textAlign: 'center' }}>
                        У вас пока нет заметок. Создайте первую!
                    </Typography>
                ) : (
                    <Grid container spacing={3}>
                        {notes.map((note) => (
                            <Grid item xs={12} sm={6} md={4} key={note.id}>
                                <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                                    <CardContent sx={{ flexGrow: 1 }}>
                                        <Typography variant="h6" component="h2" gutterBottom>
                                            {note.title}
                                        </Typography>
                                        <Typography variant="body2" color="text.secondary" sx={{
                                            mb: 2,
                                            overflow: 'hidden',
                                            textOverflow: 'ellipsis',
                                            display: '-webkit-box',
                                            WebkitLineClamp: 3,
                                            WebkitBoxOrient: 'vertical',
                                        }}>
                                            {note.content}
                                        </Typography>
                                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                            {note.tags.map((tag) => (
                                                <Chip key={tag} label={tag} size="small" />
                                            ))}
                                        </Box>
                                    </CardContent>
                                    <CardActions>
                                        <IconButton
                                            size="small"
                                            color="primary"
                                            onClick={() => handleOpenDialog(note)}
                                        >
                                            <EditIcon />
                                        </IconButton>
                                        <IconButton
                                            size="small"
                                            color="error"
                                            onClick={() => handleDeleteNote(note.id)}
                                        >
                                            <DeleteIcon />
                                        </IconButton>
                                    </CardActions>
                                </Card>
                            </Grid>
                        ))}
                    </Grid>
                )}
            </Box>

            {/* Диалог создания/редактирования заметки */}
            <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
                <DialogTitle>
                    {editingNote ? 'Редактировать заметку' : 'Создать заметку'}
                </DialogTitle>
                <DialogContent>
                    <TextField
                        autoFocus
                        margin="dense"
                        name="title"
                        label="Заголовок"
                        type="text"
                        fullWidth
                        variant="outlined"
                        value={formData.title}
                        onChange={handleInputChange}
                        sx={{ mb: 2 }}
                    />
                    <TextField
                        margin="dense"
                        name="content"
                        label="Содержание"
                        multiline
                        rows={4}
                        fullWidth
                        variant="outlined"
                        value={formData.content}
                        onChange={handleInputChange}
                        sx={{ mb: 2 }}
                    />
                    <TextField
                        margin="dense"
                        name="tags"
                        label="Теги (через запятую)"
                        type="text"
                        fullWidth
                        variant="outlined"
                        value={formData.tags}
                        onChange={handleInputChange}
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleCloseDialog}>Отмена</Button>
                    <Button onClick={handleSaveNote} variant="contained">Сохранить</Button>
                </DialogActions>
            </Dialog>

            {/* Уведомление */}
            <Snackbar
                open={snackbar.open}
                autoHideDuration={6000}
                onClose={handleCloseSnackbar}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
            >
                <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
                    {snackbar.message}
                </Alert>
            </Snackbar>
        </Container>
    );
};

export default Notes; 