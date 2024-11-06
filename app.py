import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { ArrowRight, AlertCircle, CheckCircle2, Clock } from 'lucide-react';

const EstimIA = () => {
  const [step, setStep] = useState(1);
  
  const ViewButton = ({ children, onClick, className = '' }) => (
    <button
      onClick={onClick}
      className={`
        bg-[#2F4F4F] hover:bg-[#1a2e2e] 
        text-white font-medium py-2 px-6 
        rounded transition-all duration-200 
        flex items-center gap-2
        ${className}
      `}
    >
      {children}
    </button>
  );

  const ViewCard = ({ children, className = '' }) => (
    <div className={`
      bg-white rounded-lg shadow-md p-6 
      border-l-4 border-[#2F4F4F]
      ${className}
    `}>
      {children}
    </div>
  );

  return (
    <div className="max-w-5xl mx-auto p-6 bg-gray-50">
      {/* En-tête avec logo View */}
      <div className="flex justify-center mb-8">
        <img 
          src="/api/placeholder/200/80" 
          alt="View Avocats"
          className="h-20"
        />
      </div>

      {/* Titre principal avec style View */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-[#2F4F4F] mb-4">
          Estim'IA by View Avocats
        </h1>
        <p className="text-gray-600 text-lg">
          Estimation gratuite et immédiate de vos prestations juridiques
        </p>
      </div>

      {/* Points clés */}
      <div className="grid md:grid-cols-3 gap-6 mb-12">
        <ViewCard>
          <div className="flex items-start gap-4">
            <Clock className="text-[#2F4F4F] h-8 w-8 mt-1" />
            <div>
              <h3 className="font-semibold text-[#2F4F4F] mb-2">Rapide</h3>
              <p className="text-gray-600">Estimation en moins de 2 minutes</p>
            </div>
          </div>
        </ViewCard>

        <ViewCard>
          <div className="flex items-start gap-4">
            <CheckCircle2 className="text-[#2F4F4F] h-8 w-8 mt-1" />
            <div>
              <h3 className="font-semibold text-[#2F4F4F] mb-2">Fiable</h3>
              <p className="text-gray-600">IA entraînée sur nos prestations</p>
            </div>
          </div>
        </ViewCard>

        <ViewCard>
          <div className="flex items-start gap-4">
            <AlertCircle className="text-[#2F4F4F] h-8 w-8 mt-1" />
            <div>
              <h3 className="font-semibold text-[#2F4F4F] mb-2">Sans engagement</h3>
              <p className="text-gray-600">Simple estimation indicative</p>
            </div>
          </div>
        </ViewCard>
      </div>

      {/* Formulaire principal */}
      <Card className="mb-8">
        <CardHeader className="border-b bg-gray-50">
          <CardTitle className="text-[#2F4F4F]">
            Décrivez votre situation
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Vous êtes :
              </label>
              <select className="w-full p-2 border rounded focus:ring-2 focus:ring-[#2F4F4F] focus:border-transparent">
                <option value="particulier">Particulier</option>
                <option value="professionnel">Professionnel</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Degré d'urgence :
              </label>
              <select className="w-full p-2 border rounded focus:ring-2 focus:ring-[#2F4F4F] focus:border-transparent">
                <option value="normal">Normal</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Votre situation :
              </label>
              <textarea 
                className="w-full p-3 border rounded h-32 focus:ring-2 focus:ring-[#2F4F4F] focus:border-transparent"
                placeholder="Décrivez votre situation juridique en quelques lignes..."
              />
            </div>

            <ViewButton className="w-full justify-center">
              Obtenir une estimation gratuite
              <ArrowRight className="h-4 w-4" />
            </ViewButton>
          </div>
        </CardContent>
      </Card>

      {/* Footer avec mentions légales */}
      <div className="text-center text-sm text-gray-500">
        <p>© 2024 View Avocats - Cabinet d'avocats en droit des affaires</p>
        <p className="mt-1">
          Cette estimation est fournie à titre indicatif et ne constitue pas un engagement contractuel
        </p>
      </div>
    </div>
  );
};

export default EstimIA;
