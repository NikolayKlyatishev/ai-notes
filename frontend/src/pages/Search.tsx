import { Clear as ClearIcon, Search as SearchIcon } from '@mui/icons-material';
import {
    Box,
    Button,
    Card,
    CardContent,
    Chip,
    CircularProgress,
    Container,
    Divider,
    Grid,
    IconButton,
    InputAdornment,
    TextField,
    Typography
} from '@mui/material';
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { apiService, Note } from '../services/api';

const Search: React.FC = () => {
    const [searchQuery, setSearchQuery] = useState('');
    const [isSearching, setIsSearching] = useState(false);
    const [searchResults, setSearchResults] = useState<Note[]>([]);
    const [totalResults, setTotalResults] = useState(0);
    const [hasSearched, setHasSearched] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSearch = async (e?: React.FormEvent) => {
        if (e) {
            e.preventDefault();
        }

        if (!searchQuery.trim()) {
            return;
        }

        try {
            setIsSearching(true);
            setError(null);

            const results = await apiService.search.query(searchQuery);

            setSearchResults(results.notes);
            setTotalResults(results.total);
            setHasSearched(true);
        } catch (err) {
            console.error('Ошибка при поиске:', err);
            setError('Не удалось выполнить поиск. Пожалуйста, попробуйте позже.');
            setSearchResults([]);
            setTotalResults(0);
        } finally {
            setIsSearching(false);
        }
    };

    const handleClearSearch = () => {
        setSearchQuery('');
        setSearchResults([]);
        setTotalResults(0);
        setHasSearched(false);
        setError(null);
    };

    const highlightMatchedText = (text: string, query: string) => {
        if (!query.trim()) return text;

        const regex = new RegExp(`(${query.trim()})`, 'gi');
        const parts = text.split(regex);

        return parts.map((part, index) =>
            regex.test(part) ? <mark key={index}>{part}</mark> : part
        );
    };

    return (
        <Container maxWidth="md">
            <Box sx={{ my: 4 }}>
                <Typography variant="h4" component="h1" gutterBottom>
                    Поиск заметок
                </Typography>

                <Box component="form" onSubmit={handleSearch} sx={{ mb: 4 }}>
                    <TextField
                        fullWidth
                        variant="outlined"
                        placeholder="Введите поисковый запрос..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        InputProps={{
                            startAdornment: (
                                <InputAdornment position="start">
                                    <SearchIcon />
                                </InputAdornment>
                            ),
                            endAdornment: searchQuery && (
                                <InputAdornment position="end">
                                    <IconButton onClick={handleClearSearch} edge="end">
                                        <ClearIcon />
                                    </IconButton>
                                </InputAdornment>
                            )
                        }}
                        sx={{ mb: 2 }}
                    />

                    <Button
                        variant="contained"
                        onClick={handleSearch}
                        disabled={isSearching || !searchQuery.trim()}
                        startIcon={isSearching ? <CircularProgress size={20} color="inherit" /> : <SearchIcon />}
                    >
                        {isSearching ? 'Поиск...' : 'Найти'}
                    </Button>
                </Box>

                {error && (
                    <Typography color="error" sx={{ mb: 2 }}>
                        {error}
                    </Typography>
                )}

                {hasSearched && (
                    <Box>
                        <Typography variant="body1" sx={{ mb: 2 }}>
                            {totalResults > 0
                                ? `Найдено результатов: ${totalResults}`
                                : 'По вашему запросу ничего не найдено'}
                        </Typography>

                        {searchResults.length > 0 && (
                            <Grid container spacing={3}>
                                {searchResults.map((note) => (
                                    <Grid item xs={12} key={note.id}>
                                        <Card>
                                            <CardContent>
                                                <Typography variant="h6" component="h2" gutterBottom>
                                                    {highlightMatchedText(note.title, searchQuery)}
                                                </Typography>

                                                <Typography variant="body2" color="text.secondary" paragraph>
                                                    {highlightMatchedText(note.content.substring(0, 200) + (note.content.length > 200 ? '...' : ''), searchQuery)}
                                                </Typography>

                                                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
                                                    {note.tags.map((tag) => (
                                                        <Chip key={tag} label={tag} size="small" />
                                                    ))}
                                                </Box>

                                                <Divider sx={{ mb: 2 }} />

                                                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                                    <Typography variant="caption" color="text.secondary">
                                                        Создано: {new Date(note.created_at).toLocaleDateString()}
                                                    </Typography>

                                                    <Button
                                                        component={Link}
                                                        to={`/notes/${note.id}`}
                                                        size="small"
                                                        variant="outlined"
                                                    >
                                                        Открыть
                                                    </Button>
                                                </Box>
                                            </CardContent>
                                        </Card>
                                    </Grid>
                                ))}
                            </Grid>
                        )}
                    </Box>
                )}
            </Box>
        </Container>
    );
};

export default Search; 