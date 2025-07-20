import { Film, BookOpen, Sparkles } from 'lucide-react';
import { BookCard } from './BookCard';
import { RecommendationResponse } from '@/types';

interface RecommendationResultsProps {
  recommendations: RecommendationResponse[];
  loading: boolean;
  onRegenerate: () => void;
}

export const RecommendationResults: React.FC<RecommendationResultsProps> = ({
  recommendations,
  loading,
  onRegenerate
}) => {
  console.log('RecommendationResults component received:', {
    recommendations,
    loading,
    recommendationsLength: recommendations?.length,
    firstRecommendation: recommendations?.[0]
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-medium-contrast scholarly-heading">Finding perfect book matches...</p>
        </div>
      </div>
    );
  }

  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="text-center py-12">
        <BookOpen className="w-16 h-16 text-medium-contrast mx-auto mb-4" />
        <p className="text-medium-contrast scholarly-heading">No recommendations yet. Add some movies to get started!</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-high-contrast scholarly-heading flex items-center gap-2">
          <Sparkles className="w-6 h-6 text-primary" />
          Your Book Recommendations
        </h2>
        <button
          onClick={onRegenerate}
          className="btn-secondary px-6 py-3 rounded-xl flex items-center gap-2 focusable"
        >
          <Sparkles className="w-4 h-4" />
          Regenerate
        </button>
      </div>

      {recommendations.map((recommendation, index) => (
        <div key={index} className="space-y-6">
          <div className="flex items-center gap-3 pb-4 border-b border-card-border">
            <Film className="w-5 h-5 text-primary" />
            <h3 className="text-xl font-semibold text-high-contrast scholarly-heading">
              Based on your taste for {recommendation.movie}
            </h3>
          </div>
          
          <div className="grid gap-4">
            {recommendation.books.map((book, bookIndex) => (
              <BookCard key={bookIndex} book={book} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};