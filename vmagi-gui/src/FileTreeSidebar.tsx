import { useState } from 'react';
import { useMagiStore } from './store';

const FileTreeNode = ({ node, level, onFileClick }: { node: any, level: number, onFileClick: (path: string) => void }) => {
  const [isOpen, setIsOpen] = useState(false);
  const isFolder = node.type === 'folder';

  return (
    <div>
      {/* Un nodo del árbol es un control: abre una carpeta o un fichero.
          Era un `<div onClick>`, así que el árbol entero —que puede tener
          cientos de entradas— no existía para el teclado. */}
      <button
        type="button"
        style={{
          paddingLeft: `${level * 10}px`,
          width: '100%',
          border: 0,
          background: 'none',
          textAlign: 'left',
          font: 'inherit',
          cursor: 'pointer',
          color: isFolder ? 'var(--node)' : '#cfe0e4',
          display: 'flex',
          alignItems: 'center',
          padding: '2px 0',
          fontSize: '12px'
        }}
        aria-expanded={isFolder ? isOpen : undefined}
        onClick={() => {
          if (isFolder) {
            setIsOpen(!isOpen);
          } else if (node.path) {
            onFileClick(node.path);
          }
        }}
        className="file-node-hover"
      >
        <span aria-hidden="true" style={{ width: '16px', display: 'inline-block', marginRight: '4px', textAlign: 'center' }}>
          {isFolder ? (isOpen ? '📂' : '📁') : '📄'}
        </span>
        {node.name}
      </button>
      {isFolder && isOpen && node.children && (
        <div>
          {node.children.map((child: any, idx: number) => (
            <FileTreeNode key={idx} node={child} level={level + 1} onFileClick={onFileClick} />
          ))}
        </div>
      )}
    </div>
  );
};

export const FileTreeSidebar = ({ onFileClick }: { onFileClick: (path: string) => void }) => {
  const { fileTree } = useMagiStore();

  return (
    <div className="col" style={{ flex: '0 0 250px', borderRight: '1px solid var(--gr)', display: 'flex', flexDirection: 'column', background: '#050809' }}>
      <div style={{ padding: '10px', borderBottom: '1px solid var(--gr)', fontWeight: 'bold', color: 'var(--dim)', fontSize: '11px', textTransform: 'uppercase' }}>
        Explorador de Archivos
      </div>
      <div style={{ flex: 1, overflowY: 'auto', padding: '10px' }}>
        {fileTree.length > 0 ? (
          fileTree.map((node: any, idx: number) => (
            <FileTreeNode key={idx} node={node} level={0} onFileClick={onFileClick} />
          ))
        ) : (
          <div style={{ color: 'var(--dim)', fontSize: '12px' }}>Cargando árbol de archivos...</div>
        )}
      </div>
    </div>
  );
};
